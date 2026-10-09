#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 14 January 2026

import csv
import gzip
import json
from dataclasses import KW_ONLY
from datetime import date, datetime
from io import StringIO
from typing import Literal, Protocol, runtime_checkable
from zoneinfo import ZoneInfo

from pydantic import validate_call
from pydantic.dataclasses import dataclass

from . import value_objects


@validate_call(validate_return=True)
def now(tz: ZoneInfo = value_objects.TIME_ZONE) -> datetime:
    return datetime.now(tz)


@validate_call(validate_return=True)
def today(tz: ZoneInfo = value_objects.TIME_ZONE) -> date:
    return now(tz).date()


@runtime_checkable
class Transform(Protocol):
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __call__(self, data: value_objects.Data) -> value_objects.Data: ...


# Gzip
@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def compress_to_gzip(data: value_objects.Data) -> value_objects.Data:
    if not isinstance(data, str) and not isinstance(data, bytes):
        data: str = str(data)

    if not isinstance(data, bytes):
        data: bytes = data.encode(value_objects.ENCODING)

    return gzip.compress(data, compresslevel=9)


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def decompress_from_gzip(data: value_objects.Data) -> value_objects.Data:
    return gzip.decompress(data)


# CSV
@dataclass(frozen=True)
class DumpsToCsv(Transform):
    _: KW_ONLY
    delimiter: Literal[
        # Risk level    : Very Low
        # Based Used For: Natural text, mixed content, copy-pasting
        "TAB",
        # Risk level    : Very Low
        # Based Used For: Databases, logs, text heavy data
        "PIPE",
        # Risk level    : Medium
        # Based Used For: European regional data, standard tables
        "SEMICOLON",
        # Risk level    : High (without quotes)
        # Based Used For: Strictly numeric or fully escaped data
        "COMMA",
        # Risk level    : Zero
        # Based Used For: Automated backend system-to-system transfers
        "UNIT-SEPARATOR",
        # Risk level    : Zero
        # Based Used For: Automated backend system-to-system transfers
        "RECORD-SEPARATOR",
    ] = "COMMA"
    line_terminator: str = "\n"
    has_header: bool = True
    quoting: Literal[
        "QUOTE_ALL",
        "QUOTE_MINIMAL",
        "QUOTE_NONE",
        "QUOTE_NONNUMERIC",
    ] = "QUOTE_ALL"

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __call__(self, data: value_objects.Data) -> value_objects.Data:
        csv_file: StringIO | None = None
        delimiters: dict = {
            "TAB": "\t",
            "PIPE": "|",
            "SEMICOLON": ";",
            "COMMA": ",",
            "UNIT-SEPARATOR": "\x1f",
            "RECORD-SEPARATOR": "\x1e",
        }

        for i, row in enumerate(data):
            if i == 0:
                csv_file = StringIO()
                csv_writer: csv.DictWriter = csv.DictWriter(
                    csv_file,
                    fieldnames=row.keys(),
                    delimiter=delimiters[self.delimiter],
                    lineterminator=self.line_terminator,
                    quoting=getattr(csv, self.quoting),
                )

                if self.has_header:
                    csv_writer.writeheader()

            csv_writer.writerow(row)

        if csv_file:
            csv_file.seek(0)

        return csv_file


# JSON
@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def dumps_to_json(data: value_objects.Data) -> value_objects.Data:
    return json.dumps(data, default=str)


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def loads_from_json(data: value_objects.Data) -> value_objects.Data:
    return json.loads(data)
