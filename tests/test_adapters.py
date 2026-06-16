#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 10 May 2026

from collections.abc import Callable

from duckdb import DuckDBPyConnection
from sqlalchemy import Engine

from voxrow.core.adapters.utils.database import duckdb, sqlmodel
from voxrow.core.adapters.utils.storage import boto3
from voxrow.core.domain import value_objects


class TestDatabase:
    def test_duckdb(
        self,
        fake_boto3_credential: value_objects.Boto3Credential,
        fake_duckdb_conn: DuckDBPyConnection,
        fake_db_dsn: value_objects.DatabaseType,
    ) -> None:
        duckdb.connect_to_r2(
            fake_duckdb_conn,
            fake_boto3_credential,
        )

        assert (
            duckdb.get_schema(
                fake_duckdb_conn,
                fake_db_dsn,
                "db",
            )
            == value_objects.DEFAULT_SCHEMA
        )

    def test_sqlmodel(self, fake_db_engine: Engine) -> None:
        assert sqlmodel.get_schema(fake_db_engine) == value_objects.DEFAULT_SCHEMA


class TestStorage:
    def test_boto3(
        self,
        fake_bucket: str,
        fake_boto3_credential: value_objects.Boto3Credential,
        mock_boto3: Callable,  # noqa: ARG002
    ) -> None:
        params: tuple = (fake_boto3_credential, fake_bucket, "old/")
        boto3.moves(*params, "new/", boto3.all_location(*params))
