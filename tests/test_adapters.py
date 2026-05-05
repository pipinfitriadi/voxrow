#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 5 May 2026

from duckdb import DuckDBPyConnection, connect
from pydantic import validate_call
from pydantic.dataclasses import dataclass

from voxrow.core.adapters.ports import duckdb
from voxrow.core.domain import value_objects


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class FakeTransformDuckDB(duckdb.AbstractDuckDB):
    @validate_call
    def __call__(self, data: value_objects.Data) -> value_objects.Data:
        self.register(data)

        yield from self.get_data(
            self.connection.query(f"SELECT * FROM {self.view_name};")  # noqa: S608
        )


class TestPorts:
    def test_tranform_duckdb(self) -> None:
        conn: DuckDBPyConnection = connect()
        data: tuple[dict, ...] = (dict(a=1),)

        assert (
            tuple(FakeTransformDuckDB(conn, "test_table", 5, as_iterator=True)(data))
            == data
        )
