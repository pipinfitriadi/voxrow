#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 October 2026

from google.cloud.storage import Client
from pydantic import AnyUrl, validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractDataPort


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
        data: value_objects.Data,  # noqa: ARG002
        *,
        destination: value_objects.GcsDestination,  # noqa: ARG002
    ) -> value_objects.ResourceLocation:
        return AnyUrl(f"{value_objects.Boto3Scheme.gs}://examplebucket/with-header.csv")
