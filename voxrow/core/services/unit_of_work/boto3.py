#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 25 January 2026

from pydantic import validate_call

from ...adapters.ports import boto3
from ...adapters.utils.storage import boto3 as storage_boto3
from ...domain import value_objects
from . import AbstractDataUnitOfWork


class Boto3DataUnitOfWork(AbstractDataUnitOfWork):
    @validate_call
    def __init__(
        self,
        credential: value_objects.Boto3Credential,
        scheme: value_objects.Boto3Scheme,
    ) -> None:
        self.data = boto3.Boto3DataPort(storage_boto3.get_client(credential), scheme)
