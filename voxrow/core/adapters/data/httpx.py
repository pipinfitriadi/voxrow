#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 January 2026

from http import HTTPMethod

from httpx import Response, get, post
from pydantic import validate_call

from ...domain.value_objects import (
    Data,
    Destination,
    HttpxSource,
    ResourceLocation,
)
from . import AbstractDataPort


class HttpxDataAdapter(AbstractDataPort):
    @validate_call
    def extract(self, *, source: HttpxSource) -> Data:
        methods: dict = {
            HTTPMethod.GET: get,
            HTTPMethod.POST: post,
        }
        resp: Response = methods[source.method](
            url=str(source.url),
            verify=source.verify,
            headers=source.headers,
            **(dict(timeout=source.timeout) if source.timeout is not None else {}),
            **(dict(json=source.json) if source.method is HTTPMethod.POST else {}),
        )

        resp.raise_for_status()

        return resp.json()

    @validate_call
    async def load(
        self,
        data: Data,
        *,
        destination: Destination,
    ) -> ResourceLocation:  # pragma: no cover
        pass
