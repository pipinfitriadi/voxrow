#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 25 January 2026

from duckdb import DuckDBPyConnection
from pydantic import validate_call

from ...adapters.data import duckdb
from ...domain import value_objects
from . import AbstractDataUnitOfWork


class DuckDBDataUnitOfWork(AbstractDataUnitOfWork):
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __init__(
        self,
        connection: DuckDBPyConnection,
        view_name: str = "source",
        fetch_size: int = 500_000,
        *,
        as_iterator: bool = False,
    ) -> None:
        self.data = duckdb.DuckDBDataAdapter(
            connection,
            view_name,
            fetch_size,
            as_iterator=as_iterator,
        )
