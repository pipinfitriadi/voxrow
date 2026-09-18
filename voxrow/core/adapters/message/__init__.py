#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 18 September 2026

from abc import ABC, abstractmethod

from pydantic import validate_call

from ...domain.value_objects import CONFIG_DICT, Destination, Message, Status


class AbstractMessagePort(ABC):  # pragma: no cover
    @abstractmethod
    @validate_call(config=CONFIG_DICT, validate_return=True)
    def send(self, message: Message, *, destination: Destination) -> Status:
        pass
