#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import asyncio
import logging
from datetime import datetime, timedelta
from functools import wraps
from inspect import (
    Parameter,
    Signature,
    iscoroutinefunction,
    signature,
)
from pathlib import Path
from typing import Annotated, Literal, TypeAlias
from zoneinfo import ZoneInfo

from pydantic import NonNegativeInt, validate_call
from rich.rule import Rule
from typer import Argument, Context, Option, Typer

from ..adapters.tasks import Task
from ..domain import domain_services, value_objects

LogLevelType: TypeAlias = Annotated[  # noqa: UP040
    Literal[*value_objects.LogLevel._member_names_],
    Option(case_sensitive=False),
]


@validate_call
def get_env_file_type(typer_help: str | None = None) -> type[Path]:
    return Annotated[
        Path,
        Argument(
            exists=True,
            dir_okay=False,
            help=typer_help,
        ),
    ]


@validate_call
def get_date_type(
    tz: ZoneInfo = value_objects.TIME_ZONE,
    *,
    delta_days: NonNegativeInt = 0,
) -> type[datetime]:
    return Annotated[
        datetime,
        Option(
            formats=[value_objects.DATE_FMT],
            default_factory=(
                lambda: domain_services.now(tz) - timedelta(days=delta_days)
            ),
            show_default=(domain_services.now(tz) - timedelta(days=delta_days))
            .date()
            .isoformat(),
        ),
    ]


@validate_call
def get_log_file_type(
    typer_help: str | None = "Example: file.log",
) -> type[Path] | None:
    return Annotated[Path | None, Option(help=typer_help)]


@validate_call(config=value_objects.CONFIG_DICT)
def inject_settings(task: Task) -> Task:
    @wraps(task)
    def wrapper(
        context: Context,
        *args: value_objects.Param.args,
        **kwargs: value_objects.Param.kwargs,
    ) -> any:  # pragma: no cover
        args = tuple(
            arg
            for i, arg in enumerate(args)
            if not (i == 0 and isinstance(arg, value_objects.Settings))
        )
        kwargs = {
            key: value
            for key, value in kwargs.items()
            if not (key == "settings" and isinstance(value, value_objects.Settings))
        }
        settings: value_objects.Settings = context.obj
        logger: logging.Logger = logging.getLogger(__name__)

        settings.console.log(Rule(f"Start: {task.__name__}"))

        try:
            result: any = (
                asyncio.run(task(settings, *args, **kwargs))
                if iscoroutinefunction(task)
                else task(settings, *args, **kwargs)
            )
        except Exception:
            logger.exception("Task failed!")

        settings.console.log(Rule(f"Finish: {task.__name__}"))

        return result

    wrapper.__signature__ = Signature(
        parameters=(
            Parameter(
                "context",
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Context,
            ),
            *(
                param
                for name, param in signature(task).parameters.items()
                if name != "settings"
            ),
        )
    )

    return wrapper


@validate_call(config=value_objects.CONFIG_DICT)
def add_tasks(app: Typer, *tasks: Task) -> None:
    for task in tasks:
        app.command(task.__name__)(inject_settings(task))
