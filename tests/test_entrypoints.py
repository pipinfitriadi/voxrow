#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import logging
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING

import minify_html
import pytest
from pydantic import DirectoryPath, FilePath, PositiveInt, validate_call
from typer import Context, Typer
from typer.models import CommandInfo
from typer.testing import CliRunner, Result

from voxrow.core.adapters import tasks
from voxrow.core.domain import value_objects
from voxrow.core.entrypoints import get_console, set_logging_config, typer

if TYPE_CHECKING:
    from rich.console import Console


@pytest.fixture
def fake_env_file(tmp_path: DirectoryPath) -> FilePath:
    env_file: FilePath = tmp_path / ".env"

    env_file.write_text(data="")

    return env_file


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def fake_typer_callback_with_log(
    command: CommandInfo,
    *,
    html_file_for_error: Path,
) -> CommandInfo:
    callback: Callable | None = command.callback

    if callback:

        @wraps(callback)
        def wrapper(
            context: Context,
            *args: value_objects.Param.args,
            __callback: Callable = callback,
            **kwargs: value_objects.Param.kwargs,
        ) -> any:
            try:
                return __callback(context, *args, **kwargs)
            except Exception:
                html_file_for_error.write_text(
                    minify_html.minify(
                        context.obj.console.export_html(inline_styles=True),
                        minify_js=True,
                        minify_css=True,
                        remove_processing_instructions=True,
                    )
                )

                raise

        command.callback = wrapper

    return command


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def fake_typer_add_tasks(
    app: Typer,
    /,
    *tasks: tasks.Task,
    html_file_for_error: Path,
) -> None:
    typer.add_tasks(app, *tasks)

    app.registered_commands = [
        fake_typer_callback_with_log(command, html_file_for_error=html_file_for_error)
        for command in app.registered_commands
    ]


class TestTyper:
    app: Typer
    runner: CliRunner

    @pytest.fixture(autouse=True)
    def setup(self, fake_message: str, tmp_path: DirectoryPath) -> None:
        self.runner = CliRunner()
        self.app = Typer(no_args_is_help=True, rich_markup_mode="markdown")
        logger: logging.Logger = logging.getLogger(__name__)

        @self.app.callback()
        def callback(
            context: Context,
            env_file: typer.get_env_file_type(
                "Example `.env` file content: https://github.com/pipinfitriadi/voxrow/blob/main/template.env"
            ),
            log_level: typer.LogLevelType = value_objects.LogLevel.INFO.name,
            log_file: typer.get_log_file_type() = None,
            log_width: PositiveInt | None = 150,
        ) -> None:
            console: Console = get_console(log_file)

            if log_width and log_width > 0:
                console.width = log_width

            set_logging_config(value_objects.LogLevel[log_level], console=console)

            context.obj = value_objects.Settings(_env_file=env_file, console=console)

        @validate_call(validate_return=True)
        def command(
            settings: value_objects.Settings,  # noqa: ARG001
            date: typer.get_date_type(),
        ) -> None:
            logger.info("%s: %s", fake_message, date.date())

        @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
        async def async_generator_func(
            settings: value_objects.Settings,  # noqa: ARG001
        ) -> value_objects.Data:
            yield 1

        @validate_call(validate_return=True)
        async def async_command(
            settings: value_objects.Settings,
            a: int,
            b: int,
        ) -> None:
            async for i in async_generator_func(settings):
                logger.info("%s, %s, %s", a, i, b)

        @validate_call(validate_return=True)
        def command_shouldbe_failed(settings: value_objects.Settings) -> float:  # noqa: ARG001
            return 1 / 0

        fake_typer_add_tasks(
            self.app,
            command,
            async_command,
            command_shouldbe_failed,
            html_file_for_error=tmp_path / "error.html",
        )

    def test_command(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_env_file: FilePath,
        fake_message: str,
        tmp_path: DirectoryPath,
    ) -> None:
        env_file: str = fake_env_file.as_posix()
        result: Result = self.runner.invoke(
            self.app,
            ["--log-level", "CRITICAL", env_file, "command"],
        )

        assert len(caplog.records) == 0
        assert result.exit_code == 0

        log_file: FilePath = tmp_path / "file.log"

        log_file.write_text("")

        assert log_file.is_file()

        caplog.clear()

        test_date: str = "2026-01-01"
        test_log_message: str = f"{fake_message}: {test_date}"
        result = self.runner.invoke(
            self.app,
            ["--log-file", log_file, env_file, "command", "--date", test_date],
        )

        assert tuple((record.levelno, record.message) for record in caplog.records) == (
            (logging.INFO, test_log_message),
        )
        assert result.exit_code == 0

        for log_line, test_word in zip(
            log_file.read_text().splitlines(),
            (" Start: command ", test_log_message, " Finish: command "),
            strict=True,
        ):
            assert test_word in log_line

    def test_async_command(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_env_file: FilePath,
        tmp_path: DirectoryPath,
    ) -> None:
        result: Result = self.runner.invoke(
            self.app,
            [fake_env_file.as_posix(), "async_command", "2", "3"],
        )

        assert tuple((record.levelno, record.message) for record in caplog.records) == (
            (logging.INFO, "2, 1, 3"),
        )
        assert result.exit_code == 0
        assert not (tmp_path / "error.html").is_file()

    def test_command_shouldbe_failed(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_env_file: FilePath,
        tmp_path: DirectoryPath,
    ) -> None:
        result: Result = self.runner.invoke(
            self.app,
            ["--log-width", "100", fake_env_file.as_posix(), "command_shouldbe_failed"],
        )

        assert tuple((record.levelno, record.message) for record in caplog.records) == (
            (logging.ERROR, "Task failed!"),
        )
        assert result.exit_code != 0
        assert (tmp_path / "error.html").is_file()
