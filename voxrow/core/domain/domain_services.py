#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 14 January 2026

import gzip
import json
from datetime import date, datetime
from typing import Protocol, runtime_checkable
from zoneinfo import ZoneInfo

from pydantic import validate_call

from .value_objects import ENCODING, TIME_ZONE, Data


@validate_call(validate_return=True)
def now(tz: ZoneInfo = TIME_ZONE) -> datetime:
    return datetime.now(tz)


@validate_call(validate_return=True)
def today(tz: ZoneInfo = TIME_ZONE) -> date:
    return now(tz).date()


@runtime_checkable
class Transform(Protocol):
    @validate_call(validate_return=True)
    def __call__(self, data: Data) -> Data: ...


@validate_call(validate_return=True)
def compress_to_gzip(data: Data) -> Data:
    if not isinstance(data, str) and not isinstance(data, bytes):
        data: str = str(data)

    if not isinstance(data, bytes):
        data: bytes = data.encode(ENCODING)

    return gzip.compress(data, compresslevel=9)


@validate_call(validate_return=True)
def decompress_from_gzip(data: Data) -> Data:
    return gzip.decompress(data)


@validate_call(validate_return=True)
def dumps_to_json(data: Data) -> Data:
    return json.dumps(data, default=str)


@validate_call(validate_return=True)
def loads_from_json(data: Data) -> Data:
    return json.loads(data)
