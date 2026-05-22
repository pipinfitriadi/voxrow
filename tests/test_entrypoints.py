#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

import logging
from pathlib import Path

import pytest
from pydantic import FilePath
from typer import Context, Typer
from typer.testing import CliRunner, Result

from voxrow.core.domain import value_objects
from voxrow.core.entrypoints import set_logging_config, typer


@pytest.fixture
def fake_env_file(tmp_path: Path) -> FilePath:
    return tmp_path / ".env"


@pytest.fixture
def fake_log_msg() -> str:
    return "Test.."


class TestTyper:
    app: Typer
    runner: CliRunner

    @pytest.fixture(autouse=True)
    def setup(self, fake_log_msg: str) -> None:
        set_logging_config()

        self.runner = CliRunner()
        self.app = Typer()
        logger: logging.Logger = logging.getLogger(__name__)

        @self.app.callback()
        def callback(context: Context, env_file: FilePath) -> None:
            context.obj = value_objects.Settings(_env_file=env_file)

        @self.app.command()
        @typer.inject_settings
        def command(*, settings: value_objects.Settings) -> None:  # noqa: ARG001
            logger.info(fake_log_msg)

    def test_command(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_env_file: FilePath,
        fake_log_msg: str,
    ) -> None:
        result: Result = self.runner.invoke(
            self.app,
            [fake_env_file.as_posix(), "command"],
        )
        record: logging.LogRecord = caplog.records[0]

        assert record.levelno == logging.INFO
        assert record.msg == fake_log_msg
        assert result.exit_code == 0
