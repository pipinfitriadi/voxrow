#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 18 May 2026

from typing import TYPE_CHECKING

from google.cloud.bigquery import Client, QueryJob
from pydantic import validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractDataPort

if TYPE_CHECKING:
    from google.cloud.bigquery.table import RowIterator, _EmptyRowIterator


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class BigqueryDataAdapter(AbstractDataPort):
    client: Client

    @validate_call
    def extract(self, *, source: value_objects.BigquerySource) -> value_objects.Data:
        query_job: QueryJob = self.client.query(source.query)  # API request
        rows: RowIterator | _EmptyRowIterator = query_job.result(
            page_size=source.page_size,
        )  # Waits for query to finish

        for row in rows:
            yield dict(row)

    @validate_call
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.Destination,
    ) -> value_objects.ResourceLocation:  # pragma: no cover
        pass
