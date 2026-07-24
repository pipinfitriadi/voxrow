#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 23 July 2026

from typing import Annotated, Literal

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.utils import Buffer
from pydantic import Field, PositiveInt, validate_call
from pydantic.dataclasses import dataclass

from ....domain import value_objects


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class AbstractAesGcmEncryption:
    key: Annotated[Buffer, Field(exclude=True)]
    byteorder: Literal["little", "big"]
    aesgcm: Annotated[AESGCM, Field(None, init=False)]
    urandom_size: Annotated[PositiveInt, Field(12, init=False)]
    nonce_length: Annotated[PositiveInt, Field(8, init=False)]
    to_bytes_length: Annotated[PositiveInt, Field(4, init=False)]

    def __post_init__(self) -> None:
        self.aesgcm = AESGCM(self.key)

    @classmethod
    @validate_call(validate_return=True)
    def generate_key(cls, bit_length: Literal[128, 192, 256] = 256) -> bytes:
        return AESGCM.generate_key(bit_length)
