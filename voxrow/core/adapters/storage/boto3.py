#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 17 February 2026

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING

import boto3
from botocore.client import BaseClient
from pydantic import validate_call

from ...domain import value_objects

if TYPE_CHECKING:
    from collections.abc import Callable


@validate_call
def get_client(credential: value_objects.Boto3Credential) -> BaseClient:
    return boto3.client(
        service_name=credential.service_name,
        endpoint_url=str(credential.endpoint_url),
        aws_access_key_id=credential.aws_access_key_id.get_secret_value(),
        aws_secret_access_key=credential.aws_secret_access_key.get_secret_value(),
        region_name=credential.region_name,
    )


@validate_call
def all_location(
    credential: value_objects.Boto3Credential,
    bucket: str,
    prefix: str,
) -> tuple[dict, ...]:
    return tuple(
        content
        for page in (
            get_client(credential)
            .get_paginator("list_objects_v2")
            .paginate(Bucket=bucket, Prefix=prefix)
        )
        for content in page["Contents"]
    )


@validate_call(config=value_objects.CONFIG_DICT)
def move(
    client: BaseClient,
    bucket: str,
    source_prefix: str,
    destination_prefix: str,
    content: dict,
) -> None:
    old_key: str = content["Key"]
    new_key: str = old_key.replace(source_prefix, destination_prefix, 1)
    source: dict = dict(Bucket=bucket, Key=old_key)

    client.copy_object(  # Server-side copy
        Bucket=bucket,
        CopySource=source,
        Key=new_key,
    )
    client.delete_object(**source)


@validate_call
def moves(
    credential: value_objects.Boto3Credential,
    bucket: str,
    source_prefix: str,
    destination_prefix: str,
    contents: tuple[dict, ...],
) -> None:
    client: BaseClient = get_client(credential)
    worker: Callable = partial(
        move,
        client,
        bucket,
        source_prefix,
        destination_prefix,
    )

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(worker, contents)
