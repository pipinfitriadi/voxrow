#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import asyncio
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
    delta_days: NonNegativeInt = 0,
    tz: ZoneInfo = value_objects.TIME_ZONE,
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
    keyword: str = "settings"

    @wraps(task)
    def wrapper(
        context: Context,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> any:  # pragma: no cover
        kwargs.pop(keyword, None)

        settings: value_objects.Settings = context.obj

        settings.console.log(Rule(f"Start: {task.__name__}"))
        result: any = (
            asyncio.run(task(*args, settings=settings, **kwargs))
            if iscoroutinefunction(task)
            else task(*args, settings=settings, **kwargs)
        )

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
                if name != keyword
            ),
        )
    )

    return wrapper


@validate_call(config=value_objects.CONFIG_DICT)
def add_tasks(app: Typer, *tasks: Task) -> None:
    for task in tasks:
        app.command(task.__name__)(inject_settings(task))
