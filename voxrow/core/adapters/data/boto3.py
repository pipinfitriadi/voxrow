#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 14 January 2026

from botocore.client import BaseClient
from pydantic import AnyUrl, validate_call
from pydantic.dataclasses import dataclass

from ...domain import domain_services, value_objects
from . import AbstractDataPort


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class Boto3DataAdapter(AbstractDataPort):
    client: BaseClient
    scheme: value_objects.Boto3Scheme

    @validate_call
    def extract(self, *, source: value_objects.Boto3Source) -> value_objects.Data:
        response: any = self.client.get_object(
            Bucket=source.bucket,
            Key=str(source.key),
            ChecksumMode="DISABLED",
        )
        data: bytes = response["Body"].read().decode(value_objects.ENCODING)

        return (
            domain_services.loads_from_json(data)
            if response.get("ContentType") == value_objects.ContentType.json
            else data
        )

    @validate_call
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.Boto3Destination,
    ) -> value_objects.ResourceLocation:
        data = (
            domain_services.dumps_to_json(data)
            if destination.content_type == value_objects.ContentType.json
            else data
        )

        self.client.put_object(
            Bucket=destination.bucket,
            Key=str(destination.key),
            Body=(
                domain_services.compress_to_gzip(data)
                if destination.content_encoding == value_objects.ContentEncoding.gzip
                else data
            ),
            **(
                dict(ContentEncoding=destination.content_encoding)
                if destination.content_encoding
                else {}
            ),
            ContentType=destination.content_type,
        )

        return AnyUrl(f"{self.scheme}://{destination.bucket}/{destination.key}")
