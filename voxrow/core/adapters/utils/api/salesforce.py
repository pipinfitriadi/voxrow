#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 October 2026

from collections.abc import Iterator

from pydantic import SecretStr, validate_call

from ....domain import value_objects


class QueryJob:
    def abort(self) -> None: ...

    def delete(self) -> None: ...

    def info(self) -> value_objects.SalesforceBulkApiQueryJobInfo: ...

    def result(self) -> value_objects.Data: ...


class BulkApiV2:
    @validate_call(validate_return=True)
    def __get_token(self) -> SecretStr: ...

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
