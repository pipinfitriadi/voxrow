#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 1 March 2026

from dataclasses import KW_ONLY
from typing import Any

from duckdb import DuckDBPyConnection, DuckDBPyRelation
from pandas import DataFrame
from pydantic import validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractDataPort


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class AbstractDuckDB:
    connection: DuckDBPyConnection
    view_name: str
    fetch_size: int
    _: KW_ONLY
    as_iterator: bool

    @validate_call
    def register(self, data: value_objects.Data) -> None:
        if not isinstance(data, DuckDBPyConnection) and not isinstance(
            data,
            DuckDBPyRelation,
        ):
            self.connection.register(self.view_name, DataFrame(data))
        elif isinstance(data, DuckDBPyRelation):
            data.create_view(self.view_name)

    @validate_call(config=value_objects.CONFIG_DICT)
    def get_data(
        self,
        cursor: DuckDBPyConnection | DuckDBPyRelation,
    ) -> value_objects.Data:
        columns: tuple[str, ...] = tuple(col[0] for col in cursor.description)

        while True:
            rows: list[tuple[Any, ...]] = cursor.fetchmany(self.fetch_size)

            if not rows:
                break

            for row in rows:
                yield dict(zip(columns, row, strict=True))


class DuckDBDataAdapter(AbstractDataPort, AbstractDuckDB):
    @validate_call
    def extract(self, *, source: value_objects.DuckDBSource) -> value_objects.Data:
        data: DuckDBPyRelation = self.connection.query(
            query=source.query,
            alias=source.alias,
            params=source.params,
        )

        return self.get_data(data) if self.as_iterator else data

    @validate_call
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.DuckDBDestination,
    ) -> value_objects.ResourceLocation:
        self.register(data)
        self.connection.query(
            query=destination.query,
            alias=destination.alias,
            params=destination.params,
        )

        return destination.table
