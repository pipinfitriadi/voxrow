#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 August 2026

import logging
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

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
            raise RuntimeError(result.errorMessage)

        return result.body.response

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def get_complete_part(
        self,
        *,
        destination: value_objects.ObsDestination,
        part_number: int,
        upload_id: Any,  # noqa: ANN401
        chunk: Any | None = None,  # noqa: ANN401
    ) -> CompletePart:
        part: CompletePart = CompletePart(
            partNum=part_number,
            etag=self.client.uploadPart(
                bucketName=destination.bucket_name,
                objectKey=destination.object_key,
                partNumber=part_number,
                uploadId=upload_id,
                object=chunk,
            ).body.etag,
        )

        logger.debug(
            "Uploaded part-%d OBS's Multipart Upload: %s",
            part_number,
            destination.object_key,
        )

        return part

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

            logger.debug("Initiated OBS's Multipart Upload: %s", destination.object_key)

            if init_result.status >= FAILED_STATUS:  # pragma: no cover
                raise RuntimeError(init_result.errorMessage)

            upload_id: any = init_result.body.uploadId
            parts: list[CompletePart] = []
            part_number: int = 1
            futures: dict[Future, int] = {}

            try:
                with ThreadPoolExecutor(
                    max_workers=destination.max_workers_thread_pool_executor,
                ) as executor:
                    while True:
                        chunk: bytes | str | any = data.read(destination.chunk_size)

                        if not chunk:
                            break

                        futures[
                            executor.submit(
                                self.get_complete_part,
                                destination=destination,
                                part_number=part_number,
                                upload_id=upload_id,
                                chunk=chunk,
                            )
                        ] = part_number

                        part_number += 1

                        if (
                            len(futures) >= destination.max_workers_thread_pool_executor
                        ):  # pragma: no cover
                            done: Future = next(as_completed(futures))

                            parts.append(done.result())

                            del futures[done]

                    parts.extend(done.result() for done in as_completed(futures))
                    parts.sort(key=lambda part: part.partNum)

                result: GetResult | any = self.client.completeMultipartUpload(
                    bucketName=destination.bucket_name,
                    objectKey=destination.object_key,
                    uploadId=upload_id,
                    completeMultipartUploadRequest=CompleteMultipartUploadRequest(
                        parts
                    ),
                )

                logger.debug(
                    "Completed OBS's Multipart Upload: %s",
                    destination.object_key,
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
