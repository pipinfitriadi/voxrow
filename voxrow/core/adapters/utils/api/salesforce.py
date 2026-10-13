#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 October 2026

from collections.abc import Iterator
from http import HTTPMethod
from time import time
from typing import Annotated

from pydantic import Field, HttpUrl, PositiveInt, PrivateAttr, SecretStr, validate_call
from pydantic.dataclasses import dataclass

from ....domain import value_objects
from ....services.unit_of_work.data import httpx

# Consts
TOKEN_EXPIRATION_SECONDS: PositiveInt = 2 * 60**2


@dataclass(frozen=True)
class QueryJob:
    id: str

    def abort(self) -> None: ...

    def delete(self) -> None: ...

    def info(self) -> value_objects.SalesforceBulkApiQueryJobInfo: ...

    def result(self) -> value_objects.Data: ...


@dataclass
class BulkApiV2:
    api_version: Annotated[str, Field(frozen=True, pattern=r"v\d+\.\d+")]
    base_url: Annotated[HttpUrl, Field(frozen=True)]
    client_id: Annotated[str, Field(frozen=True)]
    client_secret: Annotated[SecretStr, Field(frozen=True)]
    _uow: httpx.HttpxDataUnitOfWork = PrivateAttr()
    _token: dict = PrivateAttr()

    def __post_init__(self) -> None:
        self._uow = httpx.HttpxDataUnitOfWork()
        self._token = {}

    @property
    @validate_call(validate_return=True)
    def access_token(self) -> SecretStr:
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
    def all_query_job(self) -> Iterator[QueryJob]:
        """
        Get Information About All Query Jobs.

        Docs: https://developer.salesforce.com/docs/platform/api-asynch/guide/query-get-all-jobs.html
        """

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def get_query_job(self, query: value_objects.SalesforceBulkApiQuery) -> QueryJob:
        """
        Salesforce's Bulk API 2.0 Query.

        Docs: https://developer.salesforce.com/docs/platform/api-asynch/guide/query-bulk-api-2-0.html
        """
        with self._uow(
            source=value_objects.HttpxSource(
                f"{self.base_url}/services/data/{self.api_version}/jobs/query",
                HTTPMethod.POST,
                headers={
                    "Content-Type": value_objects.ContentType.json,
                    "Authorization": f"Bearer {self.access_token}",
                },
                json=dict(
                    operation=query.operation,
                    query=query.query,
                    contentType=query.content_type,
                    columnDelimiter=query.column_delimiter,
                    lineEnding=query.line_ending,
                ),
            )
        ):
            return QueryJob(self._uow.data.extract(source=self._uow.source)["id"])
