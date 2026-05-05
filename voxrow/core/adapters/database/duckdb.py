#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 26 February 2026

from duckdb import DuckDBPyConnection
from pydantic import PostgresDsn, validate_call

from ...domain import value_objects


@validate_call(config=value_objects.CONFIG_DICT)
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


@validate_call(config=value_objects.CONFIG_DICT)
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
