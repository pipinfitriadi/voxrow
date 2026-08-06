#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 August 2026

import logging
from typing import TYPE_CHECKING

from obs import GetObjectRequest, ObsClient
from pydantic import validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractDataPort

if TYPE_CHECKING:
    from obs.model import GetResult

# Constants
FAILED_STATUS: int = 300

logger: logging.Logger = logging.getLogger(__name__)


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class ObsDataAdapter(AbstractDataPort):
    client: ObsClient

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def extract(self, *, source: value_objects.ObsSource) -> value_objects.Data:
        result: GetResult | any = self.client.getObject(
            bucketName=source.bucket_name,
            objectKey=source.object_key,
            getObjectRequest=GetObjectRequest(
                content_type=source.content_type,
                content_encoding=source.content_encoding,
            ),
            loadStreamInMemory=False,
        )

        if result.status >= FAILED_STATUS:  # pragma: no cover
            error_message: str = "\n".join(
                (
                    f"OBS's getObject failed: {result.errorCode}",
                    f"OBS's Request ID: {result.requestId}",
                    f"OBS's Error Code: {result.errorCode}",
                    f"OBS's Error Message: {result.errorMessage}",
                )
            )

            raise RuntimeError(error_message)

        return result.body.response

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.Destination,
    ) -> value_objects.ResourceLocation:
        pass
