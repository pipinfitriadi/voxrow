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


@dataclass
class BulkApiV2Query:
    """
    Salesforce's Bulk API 2.0 Query.

    Docs: https://developer.salesforce.com/docs/platform/api-asynch/guide/query-bulk-api-2-0.html
    """

    api_version: Annotated[float, Field(frozen=True)]
    base_url: Annotated[HttpUrl, Field(frozen=True)]
    client_id: Annotated[str, Field(frozen=True)]
    client_secret: Annotated[SecretStr, Field(frozen=True)]
    _uow: httpx.HttpxDataUnitOfWork = PrivateAttr()
    _token: dict = PrivateAttr()
    _url: HttpUrl = PrivateAttr()

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

    @validate_call(validate_return=True)
    def all(self) -> Iterator[value_objects.SalesforceQueryJobInfo]:
        """
        Get Information About All Query Jobs.

        Docs: https://developer.salesforce.com/docs/platform/api-asynch/guide/query-get-all-jobs.html
        """

    @validate_call(validate_return=True)
    def get(
        self,
        value: value_objects.SalesforceQueryJobId
        | value_objects.SalesforceQueryJobCreate,
    ) -> value_objects.SalesforceQueryJobInfo:
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
                return value_objects.SalesforceQueryJobInfo(
                    **self._uow.data.extract(source=self._uow.source)
                )
        else:
            with self._uow(
                source=value_objects.HttpxSource(
                    f"{self._url}/{value}",
                    headers=headers,
                )
            ):
                return value_objects.SalesforceQueryJobInfo(
                    **self._uow.data.extract(source=self._uow.source)
                )

    @validate_call(validate_return=True)
    def abort(self, value: value_objects.SalesforceQueryJobInfo) -> None: ...

    @validate_call(validate_return=True)
    def delete(self, value: value_objects.SalesforceQueryJobInfo) -> None: ...

    @validate_call(validate_return=True)
    def result(
        self, value: value_objects.SalesforceQueryJobInfo
    ) -> value_objects.Data: ...
