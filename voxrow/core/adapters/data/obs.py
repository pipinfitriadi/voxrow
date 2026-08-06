#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 August 2026
from typing import TYPE_CHECKING

from obs import (
    CompleteMultipartUploadRequest,
    CompletePart,
    GetObjectRequest,
    ObsClient,
)
from pydantic import AnyUrl, validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractDataPort

if TYPE_CHECKING:
    from obs.model import GetResult

# Constants
FAILED_STATUS: int = 300


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
            raise RuntimeError(result.errorMessage)

        return result.body.response

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.ObsDestination,
    ) -> value_objects.ResourceLocation:
        if isinstance(data, value_objects.ReadableStream):
            init_result: GetResult | any = self.client.initiateMultipartUpload(
                bucketName=destination.bucket_name,
                objectKey=destination.object_key,
                contentType=destination.content_type,
                encoding_type=destination.content_encoding,
            )

            if init_result.status >= FAILED_STATUS:  # pragma: no cover
                raise RuntimeError(init_result.errorMessage)

            upload_id: any = init_result.body.uploadId
            parts: list = []
            part_number: int = 1

            try:
                while True:
                    chunk: bytes | str | any = data.read(destination.chunk_size)

                    if not chunk:
                        break

                    parts.append(
                        CompletePart(
                            partNum=part_number,
                            etag=self.client.uploadPart(
                                bucketName=destination.bucket_name,
                                objectKey=destination.object_key,
                                partNumber=part_number,
                                uploadId=upload_id,
                                object=chunk,
                            ).body.etag,
                        )
                    )

                    part_number += 1

                result: GetResult | any = self.client.completeMultipartUpload(
                    bucketName=destination.bucket_name,
                    objectKey=destination.object_key,
                    uploadId=upload_id,
                    completeMultipartUploadRequest=CompleteMultipartUploadRequest(
                        parts
                    ),
                )

                if result.status >= FAILED_STATUS:  # pragma: no cover
                    raise RuntimeError(result.errorMessage)  # noqa: TRY301
            except Exception:  # pragma: no cover
                self.client.abortMultipartUpload(
                    bucketName=destination.bucket_name,
                    objectKey=destination.object_key,
                    uploadId=upload_id,
                )

                raise
            finally:
                data.close()

        return AnyUrl(
            f"{value_objects.Boto3Scheme.obs}://{destination.bucket_name}/{destination.object_key}"
        )
