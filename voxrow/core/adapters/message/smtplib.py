#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 September 2026

from email.mime.text import MIMEText
from smtplib import SMTP

from pydantic import validate_call
from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractMessagePort


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class SmtpMessageAdapter(AbstractMessagePort):
    smtp: SMTP

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def send(
        self,
        message: value_objects.SmtpMessage,
        /,
        *,
        destination: value_objects.SmtpDestination,
    ) -> value_objects.SmtpStatus:
        msg: MIMEText = MIMEText(message.content, message.type)

        msg["From"] = destination.from_sender
        msg["To"] = ", ".join(destination.to_recipients)

        if message.subject:
            msg["Subject"] = message.subject

        failed_recipients: dict = self.smtp.send_message(msg)

        return value_objects.SmtpStatus(
            not failed_recipients,
            failed_recipients or None,
        )
