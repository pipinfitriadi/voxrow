#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 24 July 2026

from io import BytesIO
from os import urandom

from pydantic import validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from ..utils.cryptography import cryptography
from . import AbstractDataPort


@dataclass(config=value_objects.CONFIG_DICT)
class AesGcmEncryptionDataAdapter(
    cryptography.AbstractAesGcmEncryption,
    AbstractDataPort,
):
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def extract(self, *, source: value_objects.EncryptionSource) -> value_objects.Data:
        counter: int = 0
        nonce: bytes | str | any = source.read(self.urandom_size)
        data: bytes = BytesIO()

        while True:
            bytes_length: bytes | str | any = source.read(self.to_bytes_length)

            if not bytes_length:
                break

            data.write(
                self.aesgcm.decrypt(
                    nonce[: self.nonce_length] + counter.to_bytes(
                        self.to_bytes_length, self.byteorder
                    ),  # Chunk Nonce: 12 == 8 + 4,
                    source.read(
                        int.from_bytes(bytes_length, self.byteorder)  # Encrypted length
                    ),  # Encrypted
                    None,
                )  # Plain text
            )

            counter += 1

        return data

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.EncryptionDestination,
    ) -> value_objects.ResourceLocation:
        if isinstance(data, value_objects.ReadableStream):
            counter: int = 0
            nonce: bytes = urandom(self.urandom_size)

            destination.write(nonce)  # Store nonce first at destination file

            while True:
                chunk: bytes | str | any = data.read(self.chunk_size)

                if not chunk:
                    break

                encrypted: bytes = self.aesgcm.encrypt(
                    nonce[: self.nonce_length]
                    + counter.to_bytes(
                        self.to_bytes_length, self.byteorder
                    ),  # Chunk Nonce: 12 == 8 + 4,
                    chunk,
                    None,
                )

                # Stored ciphertext length
                destination.write(
                    len(encrypted).to_bytes(self.to_bytes_length, self.byteorder)
                )

                destination.write(encrypted)

                counter += 1

        return destination
