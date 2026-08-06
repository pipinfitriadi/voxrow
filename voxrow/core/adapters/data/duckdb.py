#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 1 March 2026

from typing import TYPE_CHECKING

from pydantic import validate_call

from ...domain import value_objects
from ..utils.database import duckdb
from . import AbstractDataPort

if TYPE_CHECKING:
    from duckdb import DuckDBPyRelation


class DuckDBDataAdapter(duckdb.AbstractDuckDB, AbstractDataPort):
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def extract(self, *, source: value_objects.DuckDBSource) -> value_objects.Data:
        data: DuckDBPyRelation = self.connection.query(
            query=source.query,
            alias=source.alias,
            params=source.params,
        )

        return self.get_data(data) if self.as_iterator else data

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
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
