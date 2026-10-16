#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 10 May 2026

from collections.abc import Callable
from dataclasses import asdict
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

if TYPE_CHECKING:
    from google.cloud.storage import Blob, Client


# Mocks
@pytest.fixture
def mock_salesforce(
    monkeypatch: pytest.MonkeyPatch,
    test_files_dir: DirectoryPath,
) -> None:
    query_job: dict = domain_services.loads_from_json(
        (test_files_dir / "salesforce" / "query_job" / "info.json").read_text()
    )

    monkeypatch.setattr(
        "voxrow.core.adapters.data.httpx.get",
        MagicMock(
            side_effect=(
                MagicMock(
                    json=MagicMock(return_value=query_job),
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
                        json=MagicMock(return_value=query_job),
                    )
                    for _ in range(2)
                ),  # ENDPOINT: /services/data/vXX.X/jobs/query
            ),
        ),
    )


class TestApi:
    def test_salesforce(self, mock_salesforce: Callable) -> None:  # noqa: ARG002
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
        query_job: value_objects.SalesforceQueryJob = api_query.get(
            value_objects.SalesforceQueryJobCreate(**query_job_create_params)
        )

        api_query.get(query_job.id)
        api_query.abort(
            value_objects.SalesforceQueryJob(
                **dict(
                    **{
                        key: value
                        for key, value in asdict(query_job).items()
                        if key != "state"
                    },
                    state="InProgress",
                    createdById=query_job.created_by_id,
                    createdDate=query_job.created_date,
                    systemModstamp=query_job.system_modstamp,
                    concurrencyMode=query_job.concurrency_mode,
                    contentType=query_job.content_type,
                    apiVersion=query_job.api_version,
                    lineEnding=query_job.line_ending,
                    columnDelimiter=query_job.column_delimiter,
                )
            )
        )
        api_query.delete(query_job)

        assert tuple(
            row
            for row in api_query.result(
                api_query.get(
                    value_objects.SalesforceQueryJobCreate(**query_job_create_params)
                )
            )
        ) == (
            dict(Id="005R0000000UyrWIAv", Name="James Wu"),
            dict(Id="005R0000000GiwjIxx", Name="Samantha Jones"),
            dict(Id="005R0000000GiwoIAB", Name="Doug West"),
        )
        assert tuple(query_job.id for query_job in api_query.all()) == (
            "750R0000000zhfdIAA",
            "750R0000000zhjzIAA",
            "750R0000000zw4yIAA",
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
