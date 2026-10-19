#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 10 May 2026

import asyncio
import itertools
import logging
from collections.abc import Callable
from time import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from duckdb import DuckDBPyConnection
from pydantic import DirectoryPath, FilePath
from sqlalchemy import Engine

from voxrow.core.adapters.utils.api import salesforce
from voxrow.core.adapters.utils.database import duckdb, sqlmodel
from voxrow.core.adapters.utils.storage import boto3, gcs
from voxrow.core.domain import domain_services, value_objects
from voxrow.core.services import handlers
from voxrow.core.services.unit_of_work.data import pathlib

if TYPE_CHECKING:
    from pathlib import Path

    from google.cloud.storage import Blob, Client


# Mocks
@pytest.fixture
def mock_salesforce(
    monkeypatch: pytest.MonkeyPatch,
    test_files_dir: DirectoryPath,
) -> None:
    monkeypatch.setattr(
        "voxrow.core.adapters.data.httpx.get",
        MagicMock(
            side_effect=(
                *(
                    MagicMock(
                        json=MagicMock(
                            return_value=domain_services.loads_from_json(
                                (
                                    test_files_dir
                                    / "salesforce"
                                    / "query_job"
                                    / "info"
                                    / "JobComplete.json"
                                ).read_text()
                            )
                        ),
                    )
                    for _ in range(2)
                ),  # ENDPOINT: /services/data/vXX.X/jobs/query/queryJobId
                *(
                    MagicMock(
                        headers=domain_services.loads_from_json(
                            (
                                test_files_dir
                                / "salesforce"
                                / "query_job"
                                / "result"
                                / str(i)
                                / "headers.json"
                            ).read_text()
                        ),
                        text=(
                            test_files_dir
                            / "salesforce"
                            / "query_job"
                            / "result"
                            / str(i)
                            / "body.csv"
                        ).read_text(),
                    )
                    for i in range(2)
                ),  # ENDPOINT: /services/data/vXX.X/jobs/query/queryJobId/results
                *(
                    MagicMock(
                        json=MagicMock(
                            return_value=domain_services.loads_from_json(
                                (
                                    test_files_dir
                                    / "salesforce"
                                    / "query_job"
                                    / "all_info"
                                    / f"{i}.json"
                                ).read_text()
                            )
                        ),
                    )
                    for i in range(2)
                ),  # ENDPOINT: /services/data/vXX.X/jobs/query
            ),
        ),
    )
    monkeypatch.setattr("voxrow.core.adapters.data.httpx.delete", MagicMock())
    monkeypatch.setattr("voxrow.core.adapters.data.httpx.patch", MagicMock())
    monkeypatch.setattr(
        "voxrow.core.adapters.data.httpx.post",
        MagicMock(
            side_effect=(
                MagicMock(
                    json=MagicMock(
                        return_value=dict(
                            access_token="fake-access-token",  # noqa: S106
                            issued_at=str(int(time() * 1e3)),
                        )
                    ),
                ),  # ENDPOINT: /services/oauth2/token
                *(
                    MagicMock(
                        json=MagicMock(
                            return_value=domain_services.loads_from_json(
                                (
                                    test_files_dir
                                    / "salesforce"
                                    / "query_job"
                                    / "info"
                                    / "UploadComplete.json"
                                ).read_text()
                            )
                        ),
                    )
                    for _ in range(2)
                ),  # ENDPOINT: /services/data/vXX.X/jobs/query
            ),
        ),
    )


class TestApi:
    @pytest.mark.asyncio
    async def test_salesforce(
        self,
        caplog: pytest.LogCaptureFixture,
        test_files_dir: DirectoryPath,
        tmp_path: DirectoryPath,
        mock_salesforce: Callable,  # noqa: ARG002
    ) -> None:
        caplog.set_level(logging.WARNING)

        api_query: salesforce.BulkApiV2Query = salesforce.BulkApiV2Query(
            "https://INSTANCE.salesforce.com",
            "fake-client-id",
            "fake-client-secret",
            api_version=46.0,
        )
        query_job_create_params: dict = dict(
            operation="query",
            query="SELECT Id, Name FROM Account",
        )

        # Create query_job
        query_job: value_objects.SalesforceQueryJob = api_query.get(
            value_objects.SalesforceQueryJobCreate(**query_job_create_params)
        )  # state == "UploadComplete"

        assert len(tuple(api_query.result(query_job))) == 0

        for record in caplog.records:
            assert record.levelno == logging.WARNING
            assert (
                record.message
                == f"Query Job ID {query_job.id}'s state is {query_job.state}!"
            )

        api_query.abort(query_job)  # state == "Aborted"
        api_query.delete(api_query.get(query_job.id))  # query_job removed

        # Recreate query_job
        query_job = api_query.get(
            value_objects.SalesforceQueryJobCreate(**query_job_create_params)
        )  # state == "UploadComplete"

        data_for_tuple, data_for_csv = itertools.tee(
            api_query.result(
                api_query.get(query_job.id),  # state == "JobComplete"
                max_records=2,
            )
        )

        assert tuple(data_for_tuple) == (
            dict(Id="005R0000000UyrWIAv", Name="James Wu"),
            dict(Id="005R0000000GiwjIxx", Name="Samantha Jones"),
            dict(Id="005R0000000GiwoIAB", Name="Doug West"),
        )
        assert tuple(query_job.id for query_job in api_query.all()) == (
            "750R0000000zhfdIAA",
            "750R0000000zhjzIAA",
            "750R0000000zw4yIAA",
            "750R0000000zxikIAA",
        )

        filename: str = "accounts.csv"

        with (
            (tmp_path / filename).open(mode="w+") as temp_file,
            pathlib.PathDataUnitOfWork()(
                destination=value_objects.PathDestination(temp_file.name)
            ) as uow,
        ):
            file: Path = await handlers.etl(
                source=data_for_csv,
                destination=uow,
                transform=domain_services.DumpsToCsv(),
            )

        assert (
            await asyncio.to_thread(file.read_text)
            == (test_files_dir / "salesforce" / "query_job" / filename).read_text()
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
        fake_blob: str,
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
        assert blob.name == fake_blob
