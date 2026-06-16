#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 19 May 2026

from google.cloud.bigquery import Client
from pydantic import validate_call

from ...adapters.data import bigquery
from ...domain import value_objects
from ...services import unit_of_work


class BigqueryDataUnitOfWork(unit_of_work.AbstractDataUnitOfWork):
    @validate_call(config=value_objects.CONFIG_DICT)
    def __init__(self, client: Client) -> None:
        self.data = bigquery.BigqueryDataAdapter(client)
