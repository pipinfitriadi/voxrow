#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 2 March 2026

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from botocore.client import BaseClient
from duckdb import DuckDBPyConnection, connect
from pydantic import AnyUrl, DirectoryPath, FilePath
from sqlalchemy import Engine

from voxrow.core.adapters.utils.database import sqlmodel
from voxrow.core.domain import value_objects


# Mocks
@pytest.fixture
def mock_boto3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "voxrow.core.adapters.utils.storage.boto3.boto3.client",
        lambda *args, **kwargs: MagicMock(  # noqa: ARG005
            spec=BaseClient,
            copy_object=MagicMock(),
            delete_object=MagicMock(),
            get_paginator=MagicMock(
                return_value=MagicMock(
                    paginate=MagicMock(
                        return_value=(
                            dict(
                                Contents=(dict(Key="fake_file.json"),),
                            ),
                        ),
                    )
                )
            ),
            get_object=MagicMock(),
            put_object=MagicMock(),
        ),
    )


@pytest.fixture
def test_files_dir() -> DirectoryPath:
    return Path("tests") / "files"


@pytest.fixture
def fake_boto3_credential() -> value_objects.Boto3Credential:
    return value_objects.Boto3Credential(
        "https://123.r2.cloudflarestorage.com",
        "123",
        "123",
    )


@pytest.fixture
def fake_bucket() -> str:
    return "fake_bucket"


@pytest.fixture
def fake_duckdb_conn() -> DuckDBPyConnection:
    return connect()


@pytest.fixture
def fake_db_dsn(tmp_path: Path) -> value_objects.DatabaseType:
    return AnyUrl(f"sqlite:///{tmp_path}/database.sqlite3")


@pytest.fixture
def fake_db_engine(fake_db_dsn: value_objects.DatabaseType) -> Engine:
    return sqlmodel.get_db_engine(fake_db_dsn)


@pytest.fixture
def fake_google_project_id() -> str:
    return "project-id"


@pytest.fixture
def fake_google_service_account_file(test_files_dir: DirectoryPath) -> FilePath:
    return test_files_dir / "google" / "service_account.json"
