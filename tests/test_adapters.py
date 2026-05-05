#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 5 May 2026

from tempfile import NamedTemporaryFile

import pytest
from anyio import Path

from voxrow.core.adapters.ports import pathlib
from voxrow.core.domain import value_objects


class TestPorts:
    @pytest.mark.asyncio
    async def test_pathlib(self) -> None:
        with NamedTemporaryFile(mode="wb+", suffix=".dat") as temp_file:
            data: str = b"Test"
            data_port: pathlib.PathDataPort = pathlib.PathDataPort()
            file: Path = await data_port.load(
                data,
                destination=value_objects.PathDestination(
                    temp_file.name,
                    is_bytes=True,
                ),
            )

            assert file == Path(temp_file.name)
            assert data_port.extract(
                source=value_objects.PathSource(
                    file,
                    is_bytes=True,
                ),
            ) == data
