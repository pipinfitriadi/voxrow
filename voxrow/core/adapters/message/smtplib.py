#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 September 2026

from smtplib import SMTP

from pydantic.dataclasses import dataclass

from ...domain import value_objects
from . import AbstractMessagePort


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class SmtpMessageAdapter(AbstractMessagePort):
    smtp: SMTP
