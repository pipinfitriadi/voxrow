#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 September 2026

from copy import copy
from types import TracebackType
from typing import Self

from pydantic import validate_call

from ....adapters.data import AbstractDataPort
from ....domain.value_objects import CONFIG_DICT, Destination, Source
from .. import AbstractUnitOfWork


class AbstractDataUnitOfWork(AbstractUnitOfWork):
    data: AbstractDataPort
    destination: Destination
    source: Source

    @validate_call
    def __call__(
        self,
        *,
        source: Source | None = None,
        destination: Destination | None = None,
    ) -> Self:
        self.source = source
        self.destination = destination

        return copy(self)

    def __enter__(self) -> Self:
        if not any((self.source, self.destination)):
            error_info: str = "destination or source must not be empty"

            raise ValueError(error_info)

        return super().__enter__()

    @validate_call(config=CONFIG_DICT, validate_return=True)
    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        exc_traceback: TracebackType | None = None,
    ) -> bool | None:
        self.source = None
        self.destination = None

        return super().__exit__(exc_type, exc_value, exc_traceback)
