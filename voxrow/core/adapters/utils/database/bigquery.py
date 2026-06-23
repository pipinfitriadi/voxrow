#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 19 May 2026

from google.cloud.bigquery import Client, SchemaField
from google.oauth2.service_account import Credentials
from pydantic import FilePath, validate_call

from ....domain import value_objects


@validate_call
def get_client(project: str, service_account_file: FilePath) -> Client:
    return Client(
        project,
        credentials=Credentials.from_service_account_file(service_account_file),
    )


@validate_call
def schema_field_mapper(
    schema_field: value_objects.BigqquerySchemaField,
) -> SchemaField:
    return SchemaField(
        schema_field.name,
        schema_field.field_type,
        schema_field.mode,
        fields=(schema_field_mapper(field) for field in schema_field.fields),
    )
