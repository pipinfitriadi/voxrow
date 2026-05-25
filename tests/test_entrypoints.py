#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import logging
from pathlib import Path
from typing import Annotated

import pytest
from click import Choice
from pydantic import FilePath
from typer import Argument, Context, Option, Typer
from typer.testing import CliRunner, Result

from voxrow.core.domain import value_objects
from voxrow.core.entrypoints import set_logging_config, typer


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
                Argument(exists=True, dir_okay=False),
            ],
            log_level: Annotated[
                str,
                Option(
                    click_type=Choice(
                        value_objects.LogLevel._member_names_,
                        case_sensitive=False,
                    ),
                ),
            ] = value_objects.LogLevel.INFO.name,
        ) -> None:
            set_logging_config(__name__, value_objects.LogLevel[log_level])

            context.obj = value_objects.Settings(_env_file=env_file)

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
    ) -> None:
        env_file: str = fake_env_file.as_posix()
        result: Result = self.runner.invoke(
            self.app,
            ["--log-level", "CRITICAL", env_file, "command"],
        )

        assert caplog.records == []
        assert result.exit_code == 0

        result = self.runner.invoke(
            self.app,
            [env_file, "command"],
        )

        for record in caplog.records:
            assert record.levelno == logging.INFO
            assert record.msg == fake_log_msg

        assert result.exit_code == 0
