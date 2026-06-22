#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 January 2026

import logging
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import KW_ONLY
from enum import IntEnum, StrEnum
from http import HTTPMethod
from pathlib import Path
from ssl import SSLContext
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import (
    AnyUrl,
    ConfigDict,
    GetCoreSchemaHandler,
    HttpUrl,
    PostgresDsn,
    SecretStr,
)
from pydantic.dataclasses import dataclass
from pydantic_core import CoreSchema, core_schema
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console

# Constants
CONFIG_DICT = ConfigDict(arbitrary_types_allowed=True)
DATE_FMT: str = "%Y-%m-%d"
DEFAULT_SCHEMA: str = "main"
ENCODING: str = "utf-8"
LOG_TIME_FMT: str = f"[{DATE_FMT} %H:%M:%S]"
TIME_ZONE: ZoneInfo = ZoneInfo("Asia/Jakarta")


class LogLevel(IntEnum):
    CRITICAL = logging.CRITICAL
    FATAL = logging.FATAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARN  # noqa: LOG009
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


class Settings(BaseSettings):
    console: Console

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_nested_delimiter="__",
        frozen=True,
    )


type DatabaseType = PostgresDsn | AnyUrl


class Domain:
    pass


@dataclass(frozen=True)
class Table:
    name: str
    schema: str


type ResourceLocation = Table | HttpUrl | AnyUrl | Path | Any
type Row = dict[Any, Any]


class Rows(Iterator[Row]):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.chain_schema(
            [
                core_schema.is_instance_schema(Iterator),
                core_schema.generator_schema(handler.generate_schema(Row)),
            ],
        )


type Data = Rows | bytes | str | Any


class ContentEncoding(StrEnum):
    gzip = "gzip"


class ContentType(StrEnum):
    html = "text/html"
    json = "application/json"
    svg = "image/svg+xml"
    xml = "application/xml"


class DbDialect(StrEnum):
    postgresql: str = "postgresql"
    sqlite: str = "sqlite"


@dataclass(frozen=True)
class Destination: ...


@dataclass(frozen=True)
class Source: ...


@dataclass(frozen=True)
class BigqquerySchemaField:
    name: str
    field_type: Literal[
        "STRING",
        "BYTES",
        "INTEGER",
        "INT64",
        "FLOAT",
        "FLOAT64",
        "BOOLEAN",
        "BOOL",
        "TIMESTAMP",
        "DATE",
        "TIME",
        "DATETIME",
        "GEOGRAPHY",
        "NUMERIC",
        "BIGNUMERIC",
        "JSON",
        "RECORD",
        "STRUCT",
        "RANGE",
    ]
    mode: Literal[
        "NULLABLE",
        "REQUIRED",
        "REPEATED",
    ] = "NULLABLE"
    fields: Iterable["BigqquerySchemaField"] = ()


@dataclass(frozen=True)
class BigquerySource(Source):
    query: str
    page_size: int | None = None


@dataclass(frozen=True)
class BigqueryDestination(Destination):
    table_id: str
    dataset_id: str
    project_id: str
    schema: Sequence[BigqquerySchemaField] | None = None
    write_disposition: Literal[
        "WRITE_APPEND",
        "WRITE_TRUNCATE",
        "WRITE_TRUNCATE_DATA",
        "WRITE_EMPTY",
    ] = "WRITE_APPEND"


@dataclass(frozen=True)
class Boto3Credential:
    endpoint_url: HttpUrl
    aws_access_key_id: SecretStr
    aws_secret_access_key: SecretStr
    region_name: str = "auto"
    service_name: str = "s3"


@dataclass(frozen=True)
class Boto3Domain:
    bucket: str
    key: Path


class Boto3Scheme(StrEnum):
    gs = "gs"
    r2 = "r2"
    s3 = "s3"


@dataclass(frozen=True)
class Boto3Destination(Destination, Boto3Domain):
    content_type: ContentType
    content_encoding: ContentEncoding | None = None


@dataclass(frozen=True)
class Boto3Source(Source, Boto3Domain):
    pass


@dataclass(frozen=True)
class DuckDBQuery:
    query: str
    alias: str = ""
    params: object | None = None


@dataclass(frozen=True, kw_only=True)
class DuckDBDestination(Destination, DuckDBQuery):
    table: Table


@dataclass(frozen=True)
class DuckDBSource(Source, DuckDBQuery):
    pass


@dataclass(frozen=True)
class SQLModelDestination(Destination):
    model: type[Domain]


@dataclass(frozen=True)
class SQLModelSource(Source):
    query: Any


@dataclass(frozen=True)
class PathDomain:
    file: Path
    encoding: str | None = None
    errors: str | None = None
    _: KW_ONLY
    is_bytes: bool = False


@dataclass(frozen=True)
class PathDestination(Destination, PathDomain):
    newline: str | None = None


@dataclass(frozen=True)
class PathSource(Source, PathDomain):
    pass


@dataclass(config=CONFIG_DICT, frozen=True)
class HttpxSource(Source):
    url: HttpUrl
    method: HTTPMethod = HTTPMethod.GET
    headers: dict | None = None
    json: Any | None = None
    timeout: float | None = None
    verify: SSLContext | str | bool = True
