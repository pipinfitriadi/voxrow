#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 24 July 2026

from typing import Literal

from cryptography.utils import Buffer
from pydantic import validate_call

from ...adapters.data import cryptography
from ...domain import value_objects
from . import AbstractDataUnitOfWork


class AesGcmEncryptionDataUnitOfWork(AbstractDataUnitOfWork):
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __init__(
        self,
        key: Buffer,
        byteorder: Literal["little", "big"] = "big",
    ) -> None:
        self.data = cryptography.AesGcmEncryptionDataAdapter(key, byteorder)
