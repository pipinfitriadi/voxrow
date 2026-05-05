#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 January 2026

from abc import ABC, abstractmethod

from pydantic import validate_call

from ...domain.value_objects import Data, Destination, ResourceLocation, Source


class AbstractDataPort(ABC):  # pragma: no cover
    @abstractmethod
    @validate_call
    def extract(self, *, source: Source) -> Data:
        pass

    @abstractmethod
    @validate_call
    async def load(
        self,
        data: Data,
        *,
        destination: Destination,
    ) -> ResourceLocation:
        pass
