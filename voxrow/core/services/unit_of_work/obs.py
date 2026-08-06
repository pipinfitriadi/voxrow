#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 August 2026

from pydantic import HttpUrl, SecretStr, validate_call

from ...adapters.data import obs
from ...adapters.utils.storage.obs import get_client
from . import AbstractDataUnitOfWork


class ObsDataUnitOfWork(AbstractDataUnitOfWork):
    @validate_call(validate_return=True)
    def __init__(
        self,
        access_key_id: SecretStr,
        secret_access_key: SecretStr,
        server: HttpUrl,
    ) -> None:
        self.data = obs.ObsDataAdapter(
            get_client(access_key_id, secret_access_key, server)
        )
