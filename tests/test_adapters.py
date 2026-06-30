#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 10 May 2026

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from duckdb import DuckDBPyConnection
from google.api_core.page_iterator import HTTPIterator
from google.cloud.storage import Blob, Client
from google.oauth2.service_account import Credentials
from pydantic import FilePath
from sqlalchemy import Engine

from voxrow.core.adapters.utils.database import duckdb, sqlmodel
from voxrow.core.adapters.utils.storage import boto3, gcs
from voxrow.core.domain import value_objects


# Mocks
@pytest.fixture
def mock_gcs(fake_bucket: str, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_blob: MagicMock = MagicMock(spec=Blob)

    mock_blob.configure_mock(name="directory/file.txt", bucket=fake_bucket)
    monkeypatch.setattr(
        "voxrow.core.adapters.utils.storage.gcs.Client",
        lambda *args, **kwargs: MagicMock(  # noqa: ARG005
            spec=Client,
            list_blobs=MagicMock(
                spec=HTTPIterator,
                return_value=(mock_blob for _ in range(1)),
            ),
        ),
    )
    monkeypatch.setattr(
        "voxrow.core.adapters.utils.storage.gcs.Credentials.from_service_account_file",
        lambda *args, **kwargs: MagicMock(spec=Credentials),  # noqa: ARG005
    )


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

    def test_gcs(
        self,
        fake_bucket: str,
        fake_google_project_id: str,
        fake_google_service_account_file: FilePath,
        mock_gcs: Callable,  # noqa: ARG002
    ) -> None:
        client: Client = gcs.get_client(
            fake_google_project_id,
            fake_google_service_account_file,
        )
        test_prefix: str = "directory"
        blob: Blob = next(client.list_blobs(fake_bucket, prefix=test_prefix))

        assert blob.bucket == fake_bucket
        assert blob.name == f"{test_prefix}/file.txt"
