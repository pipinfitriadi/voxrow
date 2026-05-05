#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 13 January 2026

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from pydantic import validate_call


class AbstractRepository(ABC):  # pragma: no cover
    @abstractmethod
    @validate_call
    def add(self, value: Any) -> any:  # noqa: ANN401
        pass

    @abstractmethod
    def all(self) -> Iterator[any]:
        pass

    @abstractmethod
    @validate_call
    def get(self, identity: Any) -> Any | None:  # noqa: ANN401
        pass
