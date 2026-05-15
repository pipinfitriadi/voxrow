#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 2 March 2026

from pathlib import Path

import pytest
from duckdb import DuckDBPyConnection, connect
from pydantic import AnyUrl
from sqlalchemy import Engine

from voxrow.core.adapters.database import sqlmodel
from voxrow.core.domain import value_objects

# Constants
TEST_FILES_DIR: Path = Path("tests") / "files"


@pytest.fixture
def fake_boto3_credential() -> value_objects.Boto3Credential:
    return value_objects.Boto3Credential(
        "https://123.r2.cloudflarestorage.com",
        "123",
        "123",
    )


@pytest.fixture
def fake_duckdb_conn() -> DuckDBPyConnection:
    return connect()


@pytest.fixture
def fake_db_dsn(tmp_path: Path) -> value_objects.DatabaseType:
    return AnyUrl(f"sqlite:///{tmp_path}/database.sqlite3")


@pytest.fixture
def fake_db_engine(fake_db_dsn: value_objects.DatabaseType) -> Engine:
    return sqlmodel.get_db_engine(fake_db_dsn)
