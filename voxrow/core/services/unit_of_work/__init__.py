#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 14 January 2026

from copy import copy
from types import TracebackType
from typing import Self

from pydantic import validate_call

from ...adapters import ports
from ...domain.value_objects import CONFIG_DICT, Destination, Source


class AbstractUnitOfWork:  # pragma: no cover
    def __enter__(self) -> Self:
        return self

    @validate_call(config=CONFIG_DICT)
    def exc_handle(
        self,
        exc_type: type[BaseException],  # noqa: ARG002
        exc_value: BaseException,  # noqa: ARG002
        exc_traceback: TracebackType,  # noqa: ARG002
    ) -> bool:
        return False

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    @validate_call(config=CONFIG_DICT)
    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        exc_traceback: TracebackType | None = None,
    ) -> bool | None:
        is_exc_suppresses: bool = False

        if exc_type:
            self.rollback()

            is_exc_suppresses = self.exc_handle(
                exc_type,
                exc_value,
                exc_traceback,
            )
        else:
            self.commit()

        return is_exc_suppresses


class AbstractDataUnitOfWork(AbstractUnitOfWork):
    data: ports.AbstractDataPort | None = None
    destination: Destination | None = None
    source: Source | None = None

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

    @validate_call(config=CONFIG_DICT)
    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        exc_traceback: TracebackType | None = None,
    ) -> bool | None:
        self.source = None
        self.destination = None

        return super().__exit__(exc_type, exc_value, exc_traceback)
