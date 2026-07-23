#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 23 July 2026

import os
from io import TextIOWrapper
from typing import Literal

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.utils import Buffer
from pydantic import validate_call

from ....domain import value_objects


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def encrypt_aesgcm(
    source: TextIOWrapper,
    destination: TextIOWrapper,
    key: Buffer,
    byteorder: Literal["little", "big"] = "big",
    *,
    chunk_size: int = 8 * 1024 * 1024,  # 8 MB
) -> None:
    aesgcm: AESGCM = AESGCM(key)
    nonce: bytes = os.urandom(12)
    counter: int = 0

    with source, destination:
        destination.write(nonce)  # Store nonce first at destination file

        while True:
            chunk: bytes | str | any = source.read(chunk_size)

            if not chunk:
                break

            chunk_nonce: bytes = nonce[:8] + counter.to_bytes(
                4, byteorder
            )  # 12 == 8 + 4
            encrypted: bytes = aesgcm.encrypt(chunk_nonce, chunk, None)

            destination.write(encrypted)

            counter += 1
