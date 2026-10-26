#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 25 January 2026

from pydantic import validate_call

from ....adapters.data import duckdb
from ....domain import value_objects
from . import AbstractDataUnitOfWork


class DuckDBDataUnitOfWork(AbstractDataUnitOfWork):
    @validate_call(validate_return=True)
    def __init__(self, config: value_objects.DuckDBConfig) -> None:
        self.data = duckdb.DuckDBDataAdapter(
            config.connection,
            config.view_name,
            fetch_size=config.fetch_size,
            as_iterator=config.as_iterator,
        )
