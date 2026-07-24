#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 23 July 2026

from dataclasses import KW_ONLY, field
from typing import Literal

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.utils import Buffer
from pydantic import Field, PositiveInt, validate_call
from pydantic.dataclasses import dataclass

from ....domain import value_objects

# Constants
CHUNK_SIZE: PositiveInt = 8 * (1_024**2)  # 8 MB


@dataclass(config=value_objects.CONFIG_DICT)
class AbstractAesGcmEncryption:
    key: Buffer = Field(exclude=True)
    byteorder: Literal["little", "big"] = "big"
    aesgcm: AESGCM = field(default=None, init=False)
    urandom_size: int = field(default=12, init=False)
    nonce_length: int = field(default=8, init=False)
    to_bytes_length: int = field(default=4, init=False)
    _: KW_ONLY
    chunk_size: PositiveInt = CHUNK_SIZE

    def __post_init__(self) -> None:
        self.aesgcm = AESGCM(self.key)

    @classmethod
    @validate_call(validate_return=True)
    def generate_key(cls, bit_length: Literal[128, 192, 256]) -> bytes:
        return AESGCM.generate_key(bit_length)
