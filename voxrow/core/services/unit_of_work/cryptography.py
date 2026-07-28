#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 24 July 2026

from contextlib import ExitStack
from dataclasses import replace
from types import TracebackType
from typing import Literal, Self

from cryptography.utils import Buffer
from pydantic import validate_call

from ...adapters.data import cryptography
from ...domain import value_objects
from . import AbstractDataUnitOfWork


class AesGcmEncryptionDataUnitOfWork(AbstractDataUnitOfWork):
    _stack: ExitStack

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __init__(
        self,
        key: Buffer,
        byteorder: Literal["little", "big"] = "big",
    ) -> None:
        self.data = cryptography.AesGcmEncryptionDataAdapter(key, byteorder)

    def __enter__(self) -> Self:
        super().__enter__()

        self._stack = ExitStack()

        try:
            if self.source and hasattr(self.source.file, "__enter__"):
                self.source = replace(
                    self.source,
                    file=self._stack.enter_context(self.source.file),
                )

            if self.destination and hasattr(self.destination.file, "__enter__"):
                self.destination = replace(
                    self.destination,
                    file=self._stack.enter_context(self.destination.file),
                )
        except Exception:  # pragma: no cover
            self._stack.close()
            raise

        return self

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        exc_traceback: TracebackType | None = None,
    ) -> bool | None:
        try:
            return super().__exit__(exc_type, exc_value, exc_traceback)
        finally:
            self._stack.close()
