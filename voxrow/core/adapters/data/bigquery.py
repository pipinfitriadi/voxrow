#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 18 May 2026

from logging import Logger, getLogger
from typing import TYPE_CHECKING

from google.cloud.bigquery import (
    Client,
    LoadJob,
    LoadJobConfig,
    QueryJob,
    SchemaField,
    Table,
)
from pydantic import validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractDataPort

if TYPE_CHECKING:
    from google.cloud.bigquery.table import RowIterator, _EmptyRowIterator

logger: Logger = getLogger(__name__)


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
        destination: value_objects.BigqueryDestination,
    ) -> value_objects.ResourceLocation:  # pragma: no cover
        table_ref: str = (
            f"{destination.project_id}.{destination.dataset_id}.{destination.table_id}"
        )
        job: LoadJob = self.client.load_table_from_json(
            data,
            Table(table_ref),
            job_config=LoadJobConfig(
                schema=(
                    tuple(
                        SchemaField(
                            field.name,
                            field.field_type,
                            field.mode,
                            fields=field.fields,
                        )
                        for field in destination.schema
                    )
                    if destination.schema
                    else None
                ),
                write_disposition=destination.write_disposition,
            ),
        )

        job.result()

        rows: int = job.output_rows or 0

        logger.info(
            "Loaded into BigQuery %s: %s row%s",
            table_ref,
            f"{rows:,}",
            "s" if rows > 1 else "",
        )

        return table_ref
