#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 August 2026

from obs import ObsClient
from pydantic import validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractDataPort


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class ObsDataAdapter(AbstractDataPort):
    client: ObsClient

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def extract(self, *, source: value_objects.Source) -> value_objects.Data:
        pass

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.Destination,
    ) -> value_objects.ResourceLocation:
        pass
