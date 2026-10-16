#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 January 2026

import logging
from collections.abc import AsyncIterable, Iterable, Iterator, Sequence
from dataclasses import KW_ONLY
from datetime import datetime
from enum import IntEnum, StrEnum
from http import HTTPMethod
from pathlib import Path
from ssl import SSLContext
from typing import Annotated, Any, Literal, ParamSpec, Protocol, runtime_checkable
from zoneinfo import ZoneInfo

from pydantic import (
    AnyUrl,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    HttpUrl,
    IPvAnyAddress,
    NameEmail,
    PositiveInt,
    PostgresDsn,
    SecretStr,
    StringConstraints,
    validate_call,
)
from pydantic.dataclasses import dataclass
from pydantic_core import CoreSchema, core_schema
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console

# Constants
BATCH_SIZE: PositiveInt = 5_000
CHUNK_SIZE: PositiveInt = 8 * (1_024**2)  # 8 MiB
CONFIG_DICT: ConfigDict = ConfigDict(arbitrary_types_allowed=True)
CSV_DELIMITERS: dict = {
    "BACKQUOTE": "`",
    "CARET": "^",
    "COMMA": ",",
    "PIPE": "|",
    "RECORD-SEPARATOR": "\x1e",
    "SEMICOLON": ";",
    "TAB": "\t",
    "TILDE": "~",
    "UNIT-SEPARATOR": "\x1f",
}
DATE_FMT: str = "%Y-%m-%d"
DEFAULT_SCHEMA: str = "main"
ENCODING: str = "utf-8"
LOG_TIME_FMT: str = f"[{DATE_FMT} %H:%M:%S]"
TIME_ZONE: ZoneInfo = ZoneInfo("Asia/Jakarta")

type DomainName = Annotated[
    str,
    StringConstraints(
        pattern=r"^(localhost|(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9])$",
        to_lower=True,
    ),
]
type Host = Annotated[
    IPvAnyAddress | DomainName,
    Field(union_mode="left_to_right"),
]
type NetworkPort = Annotated[
    PositiveInt,
    Field(le=65_535, description="Valid network port"),
]
Param: ParamSpec = ParamSpec("Param")


# ====================================== Settings ======================================


class Settings(BaseSettings):
    console: Console

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_nested_delimiter="__",
        frozen=True,
    )


# =================================== Data & Resource ==================================


type Row = dict[Any, Any]


@runtime_checkable
class ReadableStream(Protocol):
    @validate_call(validate_return=True)
    def read(self, size: int | None = -1, /) -> bytes | str | Any: ...  # noqa: ANN401

    @validate_call(validate_return=True)
    def seek(self, pos: int, whence: int = 0, /) -> int: ...

    @validate_call(validate_return=True)
    def tell(self) -> int: ...

    @validate_call(validate_return=True)
    def close(self) -> Any: ...  # noqa: ANN401


class Rows(Iterator[Row]):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.chain_schema(
            [
                core_schema.is_instance_schema(Rows),
                core_schema.generator_schema(handler.generate_schema(Row)),
            ],
        )


@dataclass(frozen=True)
class Table:
    name: str
    schema: str


@runtime_checkable
class WritableStream(Protocol):
    @validate_call(validate_return=True)
    def write(self, data: bytes) -> int: ...


# --------------------------------------------------------------------------------------


type Data = Rows | bytes | str | ReadableStream | Any
type ResourceLocation = Table | HttpUrl | AnyUrl | Path | WritableStream | Any


# ======================================================================================

type DatabaseType = PostgresDsn | AnyUrl


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
    obs = "obs"
    r2 = "r2"
    s3 = "s3"


class CaseInsensitiveStrEnum(StrEnum):
    @classmethod
    @validate_call(validate_return=True)
    def _missing_(cls, value: Any) -> StrEnum | None:  # noqa: ANN401
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member

        return None


class ContentEncoding(StrEnum):
    gzip = "gzip"


class ContentType(StrEnum):
    binary = "application/octet-stream"
    csv = "text/csv"
    excel = "application/vnd.ms-excel"
    html = "text/html"
    json = "application/json"
    mp4 = "video/mp4"
    parquet = "application/vnd.apache.parquet"
    svg = "image/svg+xml"
    text = "text/plain"
    tsv = "text/tab-separated-values"
    urlencoded = "application/x-www-form-urlencoded"
    xml = "application/xml"


@dataclass(frozen=True)
class CsvDomain:
    _: KW_ONLY
    delimiter: Literal[
        # Risk level    : Zero
        # Based Used For: Automated backend system-to-system transfers
        "UNIT-SEPARATOR",
        # Risk level    : Zero
        # Based Used For: Automated backend system-to-system transfers
        "RECORD-SEPARATOR",
        # Risk level    : Very Low
        # Based Used For: Databases, logs, text heavy data
        "PIPE",
        # Risk level    : Very Low
        # Based Used For: Databases, logs, text heavy data
        "CARET",
        # Risk level    : Very Low
        # Based Used For: Database exports, data integration, & text-heavy tabular data
        "TAB",
        # Risk level    : Low
        # Based Used For: General-purpose CSV delimiter
        "TILDE",
        # Risk level    : Low
        # Based Used For: Alternative field delimiter to minimize conflicts with common
        #                 punctuation characters in source data
        "BACKQUOTE",
        # Risk level    : Medium
        # Based Used For: European regional data, standard tables
        "SEMICOLON",
        # Risk level    : High (without quotes)
        # Based Used For: Strictly numeric or fully escaped data
        "COMMA",
    ] = "COMMA"
    line_terminator: str = "\n"
    quoting: Literal[
        "QUOTE_ALL",
        "QUOTE_MINIMAL",
        "QUOTE_NONE",
        "QUOTE_NONNUMERIC",
    ] = "QUOTE_ALL"
    has_header: bool = True


class DbDialect(StrEnum):
    postgresql: str = "postgresql"
    sqlite: str = "sqlite"


@dataclass(frozen=True)
class DuckDBQuery:
    query: str
    alias: str = ""
    params: object | None = None


class Domain:
    pass


@dataclass(frozen=True)
class GcsDomain:
    blob_name: str
    bucket_name: str
    encoding: str = ENCODING
    _: KW_ONLY
    chunk_size: PositiveInt = CHUNK_SIZE


class LogLevel(IntEnum):
    CRITICAL = logging.CRITICAL
    FATAL = logging.FATAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARN  # noqa: LOG009
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


@dataclass(frozen=True)
class ObsDomain:
    bucket_name: str
    object_key: str
    content_type: ContentType | None = None
    content_encoding: ContentEncoding | None = None


@dataclass(frozen=True)
class PathDomain:
    file: Path
    encoding: str | None = None
    errors: str | None = None
    _: KW_ONLY
    is_bytes: bool = False


# ================================ Destination & Source ================================


@dataclass(frozen=True)
class Destination: ...


# ================================== Content & Status ==================================


@dataclass(frozen=True)
class Message: ...


@dataclass(frozen=True)
class Status:
    success: bool
    details: object | None = None


# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SmtpDestination(Destination):
    from_sender: NameEmail
    to_recipients: tuple[NameEmail, ...]


@dataclass(frozen=True)
class SmtpMessage(Message):
    type: Literal["html", "plain"]
    content: str
    subject: str | None = None


@dataclass(frozen=True)
class SmtpStatus(Status):
    details: dict[NameEmail, tuple[int, bytes]] | None = None


# ======================================= Source =======================================


@dataclass(frozen=True)
class Source: ...


# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class BigqueryDestination(Destination):
    project: str
    dataset: str
    table: str
    schema: Sequence[BigqquerySchemaField] | None = None
    write_disposition: Literal[
        "WRITE_APPEND",
        "WRITE_TRUNCATE",
        "WRITE_TRUNCATE_DATA",
        "WRITE_EMPTY",
    ] = "WRITE_APPEND"


@dataclass(frozen=True)
class BigquerySource(Source):
    query: str
    page_size: int | None = None


@dataclass(frozen=True)
class Boto3Destination(Destination, Boto3Domain):
    content_type: ContentType
    content_encoding: ContentEncoding | None = None


@dataclass(frozen=True)
class Boto3Source(Source, Boto3Domain):
    pass


@dataclass(frozen=True, kw_only=True)
class DuckDBDestination(Destination, DuckDBQuery):
    table: Table


@dataclass(frozen=True)
class DuckDBSource(Source, DuckDBQuery):
    pass


@dataclass(config=CONFIG_DICT, frozen=True)
class EncryptionDestination(Destination):
    file: WritableStream
    _: KW_ONLY
    chunk_size: PositiveInt = CHUNK_SIZE


@dataclass(config=CONFIG_DICT, frozen=True)
class EncryptionSource(Source):
    file: ReadableStream


@dataclass(frozen=True)
class GcsDestination(Destination, GcsDomain):
    content_type: ContentType | None = None


@dataclass(frozen=True)
class GcsSource(Source, GcsDomain):
    pass


@dataclass(config=CONFIG_DICT, frozen=True)
class HttpxSource(Source):
    url: HttpUrl
    method: HTTPMethod = HTTPMethod.GET
    _: KW_ONLY
    output_type: Literal["BYTES", "JSON", "TEXT"] = "JSON"
    # For HTTPMethod: Patch & POST Only
    content: str | bytes | Iterable[bytes] | AsyncIterable[bytes] | None = None
    data: dict[str, Any] | None = None
    files: dict[str, Any] | tuple[tuple[str, Any], ...] | None = None
    json: Any | None = None
    # For HTTPMethod: DELETE, GET, PATCH, & POST
    params: Any | None = None
    headers: dict | tuple | None = None
    cookies: dict[str, str] | list[tuple[str, str]] | None = None
    auth: tuple[str | bytes, str | bytes] | None = None
    proxy: HttpUrl | str | None = None
    follow_redirects: bool = False
    verify: SSLContext | str | bool = True
    timeout: float | tuple | None = None
    trust_env: bool = True


@dataclass(frozen=True)
class ObsDestination(Destination, ObsDomain):
    _: KW_ONLY
    chunk_size: PositiveInt = CHUNK_SIZE
    max_workers_thread_pool_executor: int | None = 5


@dataclass(frozen=True)
class ObsSource(Source, ObsDomain):
    pass


@dataclass(frozen=True)
class PathDestination(Destination, PathDomain):
    newline: str | None = None


@dataclass(frozen=True)
class PathSource(Source, PathDomain):
    pass


@dataclass(frozen=True)
class SQLModelDestination(Destination):
    model: type[Domain]


@dataclass(frozen=True)
class SQLModelSource(Source):
    query: Any
    _: KW_ONLY
    batch_size: PositiveInt = BATCH_SIZE


# =================================== API: Salesforce ==================================

type SalesforceJobType = Literal[
    "Classic",  # Bulk API jobs. This includes both query jobs and ingest jobs
    "V2Query",  # Bulk API 2.0 query jobs
    "V2Ingest",  # Bulk API 2.0 ingest (upload and upsert) jobs
]
type SalesforceObjectQueryLanguage = str
type SalesforceQueryJobColumnDelimiter = Literal[
    "BACKQUOTE",
    "CARET",
    "COMMA",
    "PIPE",
    "SEMICOLON",
    "TAB",
]
type SalesforceQueryJobConcurrencyMode = Literal["serial", "parallel"]
type SalesforceQueryJobContentType = Literal["CSV"]
type SalesforceQueryJobId = str
type SalesforceQueryJobLineEnding = Literal[
    "LF",  # linefeed character
    "CRLF",  # Carriage return character followed by a linefeed character
]
type SalesforceQueryJobOperation = Literal[
    # Returns data that hasn't been deleted or archived. For more information,
    # see query() in SOAP API Developer Guide.
    # https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_query.htm
    "query",
    # Returns records that have been deleted because of a merge or delete,
    # and returns information about archived Task and Event records.
    # For more information, see queryAll() in SOAP API Developer Guide.
    # https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_queryall.htm
    "queryAll",
]


@dataclass(frozen=True)
class SalesforceQueryJob:
    id: SalesforceQueryJobId
    operation: SalesforceQueryJobOperation
    object: str
    created_by_id: Annotated[str, Field(validation_alias="createdById")]
    created_date: Annotated[datetime, Field(validation_alias="createdDate")]
    system_modstamp: Annotated[datetime, Field(validation_alias="systemModstamp")]
    state: Literal[
        # The job is ready to be processed and Salesforce has put the job in the queue.
        "UploadComplete",
        # Salesforce is processing the job.
        "InProgress",
        # The job has been aborted. See Abort a Query Job.
        # https://developer.salesforce.com/docs/platform/api-asynch/guide/query-abort-job.html
        "Aborted",
        # Salesforce has finished processing the job.
        "JobComplete",
        # The job failed.
        "Failed",
    ]
    concurrency_mode: Annotated[
        SalesforceQueryJobConcurrencyMode | str,
        Field(validation_alias="concurrencyMode"),
    ]
    content_type: Annotated[
        SalesforceQueryJobContentType,
        Field(validation_alias="contentType"),
    ]
    api_version: Annotated[float, Field(validation_alias="apiVersion")]
    line_ending: Annotated[
        SalesforceQueryJobLineEnding,
        Field(validation_alias="lineEnding"),
    ]
    column_delimiter: Annotated[
        SalesforceQueryJobColumnDelimiter,
        Field(validation_alias="columnDelimiter"),
    ]
    job_type: Annotated[
        SalesforceJobType | str | None,
        Field(validation_alias="jobType"),
    ] = None
    number_records_processed: Annotated[
        int | None,
        Field(validation_alias="numberRecordsProcessed"),
    ] = None
    retries: int | None = None
    total_processing_time: Annotated[
        int | None,
        Field(validation_alias="totalProcessingTime"),
    ] = None
    is_pk_chunking_supported: Annotated[
        bool | None,
        Field(validation_alias="isPkChunkingSupported"),
    ] = None


@dataclass(frozen=True)
class SalesforceQueryJobCreate:
    operation: SalesforceQueryJobOperation
    query: SalesforceObjectQueryLanguage
    content_type: SalesforceQueryJobContentType = "CSV"
    column_delimiter: SalesforceQueryJobColumnDelimiter = "COMMA"
    line_ending: SalesforceQueryJobLineEnding = "LF"
