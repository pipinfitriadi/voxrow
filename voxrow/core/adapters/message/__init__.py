#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 18 September 2026

from abc import ABC, abstractmethod

from pydantic import validate_call

from ...domain import value_objects


class AbstractMessagePort(ABC):  # pragma: no cover
    @abstractmethod
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def send(
        self,
        message: value_objects.Message,
        *,
        destination: value_objects.Destination,
    ) -> value_objects.Status:
        pass
