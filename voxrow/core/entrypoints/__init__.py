#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import logging
from datetime import timedelta

from pydantic import validate_call
from rich.console import ConsoleRenderable
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
                f"+{timedelta(seconds=0.0 if last is None else now - last)}",
                style="dim",
            ),  # delta time
        )

        return super().render(
            record=record,
            traceback=traceback,
            message_renderable=table,
        )


@validate_call
def set_logging_config() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            DeltaRichHandler(
                show_path=False,
                markup=True,
                rich_tracebacks=True,
                log_time_format="[%Y-%m-%d %H:%M:%S]",
            )
        ],
        force=True,
    )
