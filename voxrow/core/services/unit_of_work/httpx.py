#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 29 January 2026

from ...adapters.data import httpx
from . import AbstractDataUnitOfWork


class HttpxDataUnitOfWork(AbstractDataUnitOfWork):
    def __init__(self) -> None:
        self.data = httpx.HttpxDataAdapter()
