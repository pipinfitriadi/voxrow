#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 October 2026

import logging
from collections.abc import Iterator
from dataclasses import KW_ONLY
from http import HTTPMethod
from time import time
from typing import Annotated

from pydantic import Field, HttpUrl, PositiveInt, PrivateAttr, SecretStr, validate_call
from pydantic.dataclasses import dataclass

from ....domain import domain_services, value_objects
from ....services.unit_of_work.data import httpx

# Constants
TOKEN_EXPIRATION_SECONDS: PositiveInt = 2 * 60**2

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class BulkApiV2Query:
    """
    Salesforce's Bulk API 2.0 Query.

    Docs: https://developer.salesforce.com/docs/platform/api-asynch/guide/query-bulk-api-2-0.html
    """

    base_url: Annotated[HttpUrl, Field(frozen=True)]
    client_id: Annotated[str, Field(frozen=True)]
    client_secret: Annotated[SecretStr, Field(frozen=True)]
    _uow: httpx.HttpxDataUnitOfWork = PrivateAttr()
    _token: dict = PrivateAttr()
    _url: HttpUrl = PrivateAttr()
    _: KW_ONLY
    api_version: Annotated[float, Field(frozen=True)]

    def __post_init__(self) -> None:
        self._uow = httpx.HttpxDataUnitOfWork()
        self._token = {}
        self._url = HttpUrl(
            f"{self.base_url}/services/data/v{self.api_version:.1f}/jobs/query"
        )

    @property
    @validate_call(validate_return=True)
    def _access_token(self) -> SecretStr:
        if not self._token or time() >= (
            float(self._token["issued_at"]) / 1e3 + TOKEN_EXPIRATION_SECONDS
        ):
            with self._uow(
                source=value_objects.HttpxSource(
                    f"{self.base_url}/services/oauth2/token",
                    HTTPMethod.POST,
                    headers={"Content-Type": value_objects.ContentType.urlencoded},
                    data=dict(
                        grant_type="client_credentials",
                        client_id=self.client_id,
                        client_secret=self.client_secret.get_secret_value(),
                    ),
                )
            ):
                self._token = self._uow.data.extract(source=self._uow.source)

        return SecretStr(self._token["access_token"])

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def all(
        self,
        *,
        is_pk_chunking_enabled: bool = False,
        job_type: value_objects.SalesforceJobType | None = None,
        concurrency_mode: value_objects.SalesforceQueryJobConcurrencyMode | None = None,
    ) -> Iterator[value_objects.SalesforceQueryJob]:
        """
        Get Information About All Query Jobs.

        Docs: https://developer.salesforce.com/docs/platform/api-asynch/guide/query-get-all-jobs.html
        """
        params: dict = {
            **(
                dict(isPkChunkingEnabled=is_pk_chunking_enabled)
                if is_pk_chunking_enabled
                else {}
            ),
            **(dict(jobType=job_type) if job_type else {}),
            **(dict(concurrencyMode=concurrency_mode) if concurrency_mode else {}),
        }
        headers: dict = {
            "Content-Type": value_objects.ContentType.json,
            "Authorization": f"Bearer {self._access_token}",
        }

        while True:
            with self._uow(
                source=value_objects.HttpxSource(
                    self._url,
                    headers=headers,
                    params=params,
                )
            ):
                response: dict = self._uow.data.extract(source=self._uow.source)

            for query_job in response["records"]:
                yield value_objects.SalesforceQueryJob(**query_job)

            if response["done"]:
                break

            params.update(
                queryLocator=dict(
                    HttpUrl(
                        f"http://localhost/{response['nextRecordsUrl']}"
                    ).query_params()
                )["queryLocator"]
            )

    @validate_call(validate_return=True)
    def get(
        self,
        value: value_objects.SalesforceQueryJobId
        | value_objects.SalesforceQueryJobCreate,
    ) -> value_objects.SalesforceQueryJob:
        headers: dict = {
            "Content-Type": value_objects.ContentType.json,
            "Authorization": f"Bearer {self._access_token}",
        }

        if isinstance(value, value_objects.SalesforceQueryJobCreate):
            with self._uow(
                source=value_objects.HttpxSource(
                    self._url,
                    HTTPMethod.POST,
                    headers=headers,
                    json=dict(
                        operation=value.operation,
                        query=value.query,
                        contentType=value.content_type,
                        columnDelimiter=value.column_delimiter,
                        lineEnding=value.line_ending,
                    ),
                )
            ):
                return value_objects.SalesforceQueryJob(
                    **self._uow.data.extract(source=self._uow.source)
                )
        else:
            with self._uow(
                source=value_objects.HttpxSource(
                    f"{self._url}/{value}",
                    headers=headers,
                )
            ):
                return value_objects.SalesforceQueryJob(
                    **self._uow.data.extract(source=self._uow.source)
                )

    @validate_call(validate_return=True)
    def abort(self, value: value_objects.SalesforceQueryJob) -> None:
        """
        Abort a Query Job.

        To abort a job, you must be the job's creator or have the Manage Data
        Integrations permission.
        """
        if value.state in ("UploadComplete", "InProgress"):
            with self._uow(
                source=value_objects.HttpxSource(
                    f"{self._url}/{value.id}",
                    HTTPMethod.PATCH,
                    headers={
                        "Content-Type": value_objects.ContentType.json,
                        "Authorization": f"Bearer {self._access_token}",
                    },
                    json=dict(state="Aborted"),
                )
            ):
                self._uow.data.extract(source=self._uow.source)

    @validate_call(validate_return=True)
    def delete(self, value: value_objects.SalesforceQueryJob) -> None:
        if value.state in ("JobComplete", "Aborted", "Failed"):
            with self._uow(
                source=value_objects.HttpxSource(
                    f"{self._url}/{value.id}",
                    HTTPMethod.DELETE,
                    headers=dict(Authorization=f"Bearer {self._access_token}"),
                )
            ):
                self._uow.data.extract(source=self._uow.source)

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def result(
        self,
        value: value_objects.SalesforceQueryJob,
        max_records: PositiveInt | None = None,
    ) -> value_objects.Data:
        """
        Get Results for a Query Job.

        Use the same API version to get query results that you used to create the query.
        Otherwise, the call returns a 409 error.

        In API version 50.0 and later, the order of the columns returned by the query
        is the same as the order you requested them. In version 49.0 and earlier,
        the order of the columns is returned alphabetically.
        """
        if value.state == "JobComplete":
            params: dict = {**(dict(maxRecords=max_records) if max_records else {})}
            headers: dict = {
                "Accept": value_objects.ContentType.csv,
                "Authorization": f"Bearer {self._access_token}",
            }

            while True:
                with self._uow(
                    source=value_objects.HttpxSource(
                        f"{self._url}/{value.id}/results",
                        headers=headers,
                        params=params,
                        output_type="TEXT",
                    )
                ):
                    yield from domain_services.LoadsFromCsv(
                        delimiter=value.column_delimiter,
                        line_terminator=dict(
                            LF="\n",
                            CLRF="\r\n",
                        )[value.line_ending],
                    )(self._uow.data.extract(source=self._uow.source))

                    response_headers: dict = dict(self._uow.data.response.headers)

                if locator := response_headers["sforce-locator"]:
                    params.update(locator=locator)
                else:
                    break
        else:
            logger.warning("Query Job ID %s's state is %s!", value.id, value.state)

            yield from ()
