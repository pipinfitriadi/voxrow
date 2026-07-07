#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 14 January 2026

from pydantic import validate_call

from ..domain.domain_services import Transform
from ..domain.value_objects import CONFIG_DICT, Data, ResourceLocation
from .unit_of_work import AbstractDataUnitOfWork


@validate_call(config=CONFIG_DICT, validate_return=True)
async def etl(
    *,
    source: Data | AbstractDataUnitOfWork,
    destination: AbstractDataUnitOfWork,
    transform: Transform | None = None,
) -> ResourceLocation:
    """Extract, Transform, Load."""
    if isinstance(source, AbstractDataUnitOfWork):
        with source as uow:
            source = uow.data.extract(source=uow.source)

    with destination as uow:
        resource_location: ResourceLocation = await uow.data.load(
            data=source if transform is None else transform(source),
            destination=uow.destination,
        )

    return resource_location
