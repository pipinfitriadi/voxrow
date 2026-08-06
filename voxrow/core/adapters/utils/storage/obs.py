#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 6 August 2026

from obs import ObsClient
from obs.const import READ_ONCE_LENGTH
from pydantic import HttpUrl, SecretStr, validate_call

from ....domain import value_objects


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def get_client(
    access_key_id: SecretStr,
    secret_access_key: SecretStr,
    server: HttpUrl,
    *,
    chunk_size: int = READ_ONCE_LENGTH,
) -> ObsClient:
    return ObsClient(
        access_key_id=access_key_id.get_secret_value(),
        secret_access_key=secret_access_key.get_secret_value(),
        server=str(server),
        chunk_size=chunk_size,
    )
