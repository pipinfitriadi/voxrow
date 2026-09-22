#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 14 January 2026

from pydantic import validate_call

from ..domain import domain_services, value_objects
from .unit_of_work import data, message


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
async def etl(
    *,
    source: value_objects.Data | data.AbstractDataUnitOfWork,
    destination: data.AbstractDataUnitOfWork,
    transform: domain_services.Transform | None = None,
) -> value_objects.ResourceLocation:
    """Extract, Transform, Load."""
    if isinstance(source, data.AbstractDataUnitOfWork):
        with source as uow:
            source = uow.data.extract(source=uow.source)

    with destination as uow:
        resource_location: value_objects.ResourceLocation = await uow.data.load(
            data=source if transform is None else transform(source),
            destination=uow.destination,
        )

    return resource_location


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def send_message(
    uow: message.AbstractMessageUnitOfWork,
    /,
    *,
    message: value_objects.Message,
    destination: value_objects.Destination,
) -> value_objects.Status:
    with uow:
        return uow.message.send(message, destination=destination)
