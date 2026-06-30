#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import logging
from datetime import timedelta
from pathlib import Path

from pydantic import validate_call
from rich.console import Console, ConsoleRenderable
from rich.logging import RichHandler
from rich.table import Table
from rich.text import Text
from rich.traceback import Traceback

from ..domain import value_objects


class DeltaRichHandler(RichHandler):
    @validate_call
    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002,ANN003
        super().__init__(*args, **kwargs)
        self._last: dict = {}

    @validate_call(config=value_objects.CONFIG_DICT)
    def render(
        self,
        record: logging.LogRecord,
        traceback: Traceback | None,
        message_renderable: ConsoleRenderable,
    ) -> ConsoleRenderable:
        key: str = record.name
        now: float = record.created
        last: float | None = self._last.get(key)
        self._last[key] = now
        table: Table = Table.grid(padding=1, expand=True)

        table.add_column()
        table.add_column(justify="right")
        table.add_row(
            message_renderable,  # message log
            Text(
                "" if last is None else f"+{timedelta(seconds=now - last)}",
                style="dim",
            ),  # delta time
        )

        return super().render(
            record=record,
            traceback=traceback,
            message_renderable=table,
        )


@validate_call
def get_console(log_file: Path | None = None) -> Console:
    console_kwargs: dict = dict(
        log_path=False,
        log_time_format=value_objects.LOG_TIME_FMT,
    )

    if log_file:
        console_kwargs["file"] = log_file.open("a", encoding=value_objects.ENCODING)
        console_kwargs["width"] = 200

    return Console(**console_kwargs)


@validate_call(config=value_objects.CONFIG_DICT)
def set_logging_config(
    level: value_objects.LogLevel = logging.INFO,
    fmt: str = "%(message)s",
    time_fmt: str = value_objects.LOG_TIME_FMT,
    console: Console | None = None,
    *,
    show_path: bool = False,
) -> None:
    logger: logging.Logger = logging.getLogger()

    for handler in logger.handlers:
        if isinstance(handler, DeltaRichHandler):
            logger.removeHandler(handler)

    handler: DeltaRichHandler = DeltaRichHandler(
        show_path=show_path,
        markup=True,
        rich_tracebacks=True,
        log_time_format=time_fmt,
        console=console,
    )

    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.setLevel(level)
