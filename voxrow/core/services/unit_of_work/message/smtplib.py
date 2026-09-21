#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 September 2026

from smtplib import SMTP

from pydantic import validate_call

from ....adapters.message import smtplib
from ....domain import value_objects
from . import AbstractMessageUnitOfWork


class SmtpMessageUnitOfWork(AbstractMessageUnitOfWork):
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __init__(
        self,
        host: value_objects.Host,
        port: value_objects.NetworkPort,
        local_hostname: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.message = smtplib.SmtpMessageAdapter(
            SMTP(host, port, local_hostname, timeout)
        )
