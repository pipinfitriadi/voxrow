#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

import pytest
from pydantic import FilePath
from typer import Argument, Context, Option, Typer
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
    return "Test.."


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
            env_file: Annotated[
                Path,
                Argument(
                    exists=True,
                    dir_okay=False,
                    help="Example: https://github.com/pipinfitriadi/voxrow/blob/main/template.env",
                ),
            ],
            log_level: Annotated[
                Literal[*value_objects.LogLevel._member_names_],
                Option(case_sensitive=False),
            ] = value_objects.LogLevel.INFO.name,
            log_file: Annotated[
                Path | None,
                Option(help="Example: file.log"),
            ] = None,
        ) -> None:
            console: Console = get_console(log_file)

            set_logging_config(value_objects.LogLevel[log_level], console=console)

            context.obj = value_objects.Settings(_env_file=env_file, console=console)

        @self.app.command()
        @typer.inject_settings
        def command(*, settings: value_objects.Settings) -> None:  # noqa: ARG001
            logger.info(fake_log_msg)
            logger.info(fake_log_msg)

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

        test_record: int = 2
        result = self.runner.invoke(
            self.app,
            ["--log-file", log_file, env_file, "command"],
        )

        assert len(caplog.records) == test_record

        for record in caplog.records:
            assert record.levelno == logging.INFO
            assert record.msg == fake_log_msg

        assert result.exit_code == 0

        for log_line, test_word in zip(
            log_file.read_text().splitlines(),
            (" Start: command ", fake_log_msg, fake_log_msg, " Finish: command "),
            strict=True,
        ):
            assert test_word in log_line
