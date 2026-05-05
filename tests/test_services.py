#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 January 2026

from tempfile import NamedTemporaryFile

import pytest
from anyio import Path

from voxrow.core.domain import value_objects
from voxrow.core.services.unit_of_work import pathlib


class TestUnitOfWork:
    @pytest.mark.asyncio
    async def test_path_data(self) -> None:
        with (
            NamedTemporaryFile(mode="w+", suffix=".txt") as temp_file,
            pathlib.PathDataUnitOfWork()(
                destination=value_objects.PathDestination(temp_file.name),
            ) as uow,
        ):
            data: str = "Test"
            file_path: Path = await uow.data.load(
                data,
                destination=uow.destination,
            )

            assert file_path.read_text() == data
            assert file_path == Path(temp_file.name)

        with (
            pytest.raises(
                ValueError,
                match="destination or source must not be empty",
            ),
            pathlib.PathDataUnitOfWork(),
        ):
            pass  # pragma: no cover
