#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 18 May 2026

from pydantic import validate_call

from ...domain import value_objects
from . import AbstractDataPort


class BigqueryDataPort(AbstractDataPort):
    @validate_call
    def extract(self, *, source: value_objects.Source) -> value_objects.Data:
        pass

    @validate_call
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.Destination,
    ) -> value_objects.ResourceLocation:  # pragma: no cover
        pass
