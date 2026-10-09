#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 October 2026

import logging

from google.cloud.storage import Blob, Client
from pydantic import AnyUrl, PositiveInt, validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractDataPort

# Constants
MIN_CHUNK_SIZE: PositiveInt = 256 * 1_024  # 256 KiB

logger: logging.Logger = logging.getLogger(__name__)


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class GcsDataAdapter(AbstractDataPort):
    client: Client

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def extract(
        self,
        *,
        source: value_objects.GcsSource,
    ) -> value_objects.Data:  # pragma: no cover
        pass

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.GcsDestination,
    ) -> value_objects.ResourceLocation:
        """Upload a binary stream to GCS using bounded-memory buffering."""
        if isinstance(data, value_objects.ReadableStream):
            if (
                destination.chunk_size < MIN_CHUNK_SIZE
                or destination.chunk_size % MIN_CHUNK_SIZE != 0
            ):  # pragma: no cover
                # https://docs.cloud.google.com/storage/docs/performing-resumable-uploads#chunked-upload
                error_message: str = (
                    "Chunk_Size must be a multiple of 256 KiB and at least 256 KiB."
                )

                raise ValueError(error_message)

            blob: Blob = self.client.bucket(destination.bucket_name).blob(
                destination.blob_name,
                destination.chunk_size,
            )

            if destination.content_type:
                blob.content_type = destination.content_type

            # GCS resumable upload; copy data in bounded-size blocks.
            with blob.open("wb", ignore_flush=True) as blob_writer:
                try:
                    while chunk := data.read(destination.chunk_size):
                        if isinstance(chunk, str):
                            chunk = chunk.encode(destination.encoding)

                        blob_writer.write(chunk)
                finally:
                    data.close()

            logger.debug("Completed GCS's Upload: %s", destination.blob_name)

        return AnyUrl(
            f"{value_objects.Boto3Scheme.gs}://{destination.bucket_name}/{destination.blob_name}"
        )
