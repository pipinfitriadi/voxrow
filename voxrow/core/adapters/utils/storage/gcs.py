#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 8 June 2026

from google.cloud.storage import Client
from google.oauth2.service_account import Credentials
from pydantic import FilePath, validate_call

from ....domain import value_objects


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def get_client(project: str, service_account_file: FilePath) -> Client:
    return Client(
        project,
        credentials=Credentials.from_service_account_file(service_account_file),
    )
