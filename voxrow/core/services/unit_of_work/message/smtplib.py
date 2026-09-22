#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 September 2026

from smtplib import SMTP, SMTPException
from types import TracebackType
from typing import Self

from pydantic import NonNegativeFloat, validate_call

from ....adapters.message import smtplib
from ....domain import value_objects
from . import AbstractMessageUnitOfWork


class SmtpMessageUnitOfWork(AbstractMessageUnitOfWork):
    smtp: SMTP

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __init__(
        self,
        host: value_objects.Host,
        port: value_objects.NetworkPort,
        local_hostname: str | None = None,
        timeout: NonNegativeFloat | None = None,
    ) -> None:
        self.smtp = SMTP(str(host), port, local_hostname, timeout)
        self.message = smtplib.SmtpMessageAdapter(self.smtp)

    def __enter__(self) -> Self:
        self.smtp.__enter__()

        return super().__enter__()

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        exc_traceback: TracebackType | None = None,
    ) -> bool | None:
        try:
            self.smtp.__exit__(exc_type, exc_value, exc_traceback)
        except SMTPException as error:  # pragma: no cover
            exc_type = type(error)
            exc_value = error
            exc_traceback = error.__traceback__

        return super().__exit__(exc_type, exc_value, exc_traceback)
