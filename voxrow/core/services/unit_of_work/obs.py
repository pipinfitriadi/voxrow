#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 August 2026

from obs import ObsClient
from obs.const import READ_ONCE_LENGTH
from pydantic import validate_call

from ...adapters.data import obs
from ...domain import value_objects
from . import AbstractDataUnitOfWork


class ObsDataUnitOfWork(AbstractDataUnitOfWork):
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __init__(
        self,
        client: ObsClient,
        *,
        chunk_size: int = READ_ONCE_LENGTH,
    ) -> None:
        self.data = obs.ObsDataAdapter(client, chunk_size)
