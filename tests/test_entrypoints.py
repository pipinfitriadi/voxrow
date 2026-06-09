#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import FilePath
from typer import Context, Typer
from typer.testing import CliRunner, Result

from voxrow.core.domain import value_objects
from voxrow.core.entrypoints import get_console, set_logging_config, typer

if TYPE_CHECKING:
    from rich.console import Console


@pytest.fixture
def fake_env_file(tmp_path: Path) -> FilePath:
    env_file: FilePath = tmp_path / ".env"

    env_file.write_text(data="")

    return env_file


@pytest.fixture
def fake_log_msg() -> str:
    return "Test"


class TestTyper:
    app: Typer
    runner: CliRunner

    @pytest.fixture(autouse=True)
    def setup(self, fake_log_msg: str) -> None:
        self.runner = CliRunner()
        self.app = Typer()
        logger: logging.Logger = logging.getLogger(__name__)

        @self.app.callback()
        def callback(
            context: Context,
            env_file: typer.get_env_file_type(
                "Example: https://github.com/pipinfitriadi/voxrow/blob/main/template.env"
            ),
            log_level: typer.LogLevelType = value_objects.LogLevel.INFO.name,
            log_file: typer.get_log_file_type() = None,
        ) -> None:
            console: Console = get_console(log_file)

            set_logging_config(value_objects.LogLevel[log_level], console=console)

            context.obj = value_objects.Settings(_env_file=env_file, console=console)

        def command(
            date: typer.get_date_type(),
            *,
            settings: value_objects.Settings,  # noqa: ARG001
        ) -> None:
            logger.info("%s: %s", fake_log_msg, date.date())

        typer.add_tasks(self.app, command)

    def test_command(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_env_file: FilePath,
        fake_log_msg: str,
        tmp_path: Path,
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

        test_record: int = 1
        test_date: str = "2026-01-01"
        test_log_message: str = f"{fake_log_msg}: {test_date}"
        result = self.runner.invoke(
            self.app,
            ["--log-file", log_file, env_file, "command", "--date", test_date],
        )

        assert len(caplog.records) == test_record

        for record in caplog.records:
            assert record.levelno == logging.INFO
            assert record.message == test_log_message

        assert result.exit_code == 0

        for log_line, test_word in zip(
            log_file.read_text().splitlines(),
            (" Start: command ", test_log_message, " Finish: command "),
            strict=True,
        ):
            assert test_word in log_line
