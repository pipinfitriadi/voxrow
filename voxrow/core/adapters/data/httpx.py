#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 January 2026

from http import HTTPMethod

from httpx import Response, delete, get, patch, post
from pydantic import validate_call

from ...domain.value_objects import (
    CONFIG_DICT,
    Data,
    Destination,
    HttpxSource,
    ResourceLocation,
)
from . import AbstractDataPort


class HttpxDataAdapter(AbstractDataPort):
    @validate_call(config=CONFIG_DICT, validate_return=True)
    def extract(self, *, source: HttpxSource) -> Data:
        methods: dict = {
            HTTPMethod.DELETE: delete,
            HTTPMethod.GET: get,
            HTTPMethod.PATCH: patch,
            HTTPMethod.POST: post,
        }
        resp: Response = methods[source.method](
            url=str(source.url),
            **(
                dict(
                    content=source.content,
                    data=source.data,
                    files=source.files,
                    json=source.json,
                )
                if source.method
                in (
                    HTTPMethod.PATCH,
                    HTTPMethod.POST,
                )
                else {}
            ),
            params=source.params,
            headers=source.headers,
            cookies=source.cookies,
            auth=source.auth,
            proxy=source.proxy,
            follow_redirects=source.follow_redirects,
            verify=source.verify,
            timeout=source.timeout,
            trust_env=source.trust_env,
        )

        resp.raise_for_status()

        return (
            resp.json()
            if source.output_type == "JSON"
            else (resp.text if source.output_type == "TEXT" else resp.content)
        )

    @validate_call(config=CONFIG_DICT, validate_return=True)
    async def load(
        self,
        data: Data,
        *,
        destination: Destination,
    ) -> ResourceLocation:  # pragma: no cover
        pass
