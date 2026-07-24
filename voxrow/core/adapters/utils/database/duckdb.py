#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 26 February 2026

from dataclasses import KW_ONLY
from typing import Any

from duckdb import DuckDBPyConnection, DuckDBPyRelation
from pandas import DataFrame
from pydantic import PostgresDsn, validate_call
from pydantic.dataclasses import dataclass

from ....domain import value_objects


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class AbstractDuckDB:
    connection: DuckDBPyConnection
    view_name: str
    fetch_size: int
    _: KW_ONLY
    as_iterator: bool

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def register(self, data: value_objects.Data) -> None:
        if not isinstance(data, DuckDBPyConnection) and not isinstance(
            data,
            DuckDBPyRelation,
        ):
            self.connection.register(self.view_name, DataFrame(data))
        elif isinstance(data, DuckDBPyRelation):
            data.create_view(self.view_name)

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
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


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def connect_to_r2(
    conn: DuckDBPyConnection,
    credential: value_objects.Boto3Credential,
) -> None:
    conn.execute(
        f"""
        CREATE SECRET (
            TYPE r2,
            KEY_ID '{credential.aws_access_key_id.get_secret_value()}',
            SECRET '{credential.aws_secret_access_key.get_secret_value()}',
            ACCOUNT_ID '{credential.endpoint_url.host.split(".")[0]}'
        );
        """
    )


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def get_schema(
    conn: DuckDBPyConnection,
    db_dsn: value_objects.DatabaseType,
    db_name: str,
    schema: str = value_objects.DEFAULT_SCHEMA,
) -> str:
    if isinstance(db_dsn, PostgresDsn):  # pragma: no cover
        conn.execute(
            f"""
            INSTALL postgres;
            LOAD postgres;
            ATTACH
                '{db_dsn}'
                AS "{db_name}"(TYPE postgres)
            ;
            CREATE SCHEMA
            IF NOT EXISTS
                "{db_name}"."{schema}"
            ;
            """
        )
    else:
        schema = value_objects.DEFAULT_SCHEMA

        conn.execute(
            f"""
            INSTALL sqlite;
            LOAD sqlite;
            ATTACH
                '{db_dsn.path[1:]}'
                AS "{db_name}"(TYPE sqlite)
            ;
            """
        )

    return schema
