#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 September 2026

from ....adapters.message import AbstractMessagePort
from .. import AbstractUnitOfWork


class AbstractMessageUnitOfWork(AbstractUnitOfWork):
    message: AbstractMessagePort
