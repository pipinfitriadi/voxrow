#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 January 2026

from pydantic import validate_call

from ...domain.value_objects import (
    Data,
    PathDestination,
    PathSource,
    ResourceLocation,
)
from . import AbstractDataPort


class PathDataPort(AbstractDataPort):
    @validate_call
    def extract(self, *, source: PathSource) -> Data:
        return (
            source.file.read_bytes()
            if source.is_bytes
            else source.file.read_text(
                encoding=source.encoding,
                errors=source.errors,
            )
        )

    @validate_call
    async def load(
        self,
        data: Data,
        *,
        destination: PathDestination,
    ) -> ResourceLocation:
        if destination.is_bytes:
            destination.file.write_bytes(data=data)
        else:
            destination.file.write_text(
                data=data,
                encoding=destination.encoding,
                errors=destination.errors,
                newline=destination.newline,
            )

        return destination.file
