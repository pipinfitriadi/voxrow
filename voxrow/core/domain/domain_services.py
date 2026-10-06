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
from typing import Protocol, runtime_checkable
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


@dataclass(frozen=True)
class CsvTransform(Transform):
    _: KW_ONLY
    delimiter: value_objects.Delimiter = value_objects.Delimiter.comma
    line_terminator: str = "\n"
    use_header: bool = True

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __call__(self, data: value_objects.Data) -> value_objects.Data:
        csv_file: StringIO | None = None

        for i, row in enumerate(data):
            if i == 0:
                csv_file = StringIO()
                csv_writer: csv.DictWriter = csv.DictWriter(
                    csv_file,
                    fieldnames=row.keys(),
                    delimiter=self.delimiter,
                    lineterminator=self.line_terminator,
                )

                if self.use_header:
                    csv_writer.writeheader()

            csv_writer.writerow(row)

        if csv_file:
            csv_file.seek(0)

        return csv_file


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


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def dumps_to_json(data: value_objects.Data) -> value_objects.Data:
    return json.dumps(data, default=str)


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def loads_from_json(data: value_objects.Data) -> value_objects.Data:
    return json.loads(data)
