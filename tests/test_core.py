#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 January 2026

import gzip
from tempfile import NamedTemporaryFile

import pytest
from anyio import Path
from duckdb import DuckDBPyConnection, connect
from pydantic import validate_call
from pydantic.dataclasses import dataclass

from voxrow.core.adapters.ports import duckdb
from voxrow.core.domain import domain_services, value_objects
from voxrow.core.domain.value_objects import ENCODING, PathDestination
from voxrow.core.services.unit_of_work import pathlib

# Constants
TEST_DATA_FOR_GZIP: tuple = (1, 2, 3)
TEST_DATA_FOR_GZIP_BYTES: bytes = str(TEST_DATA_FOR_GZIP).encode(ENCODING)


@pytest.fixture
def fake_gzip() -> bytes:
    return gzip.compress(TEST_DATA_FOR_GZIP_BYTES, compresslevel=9)


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class FakeTransformDuckDB(duckdb.AbstractDuckDB):
    @validate_call
    def __call__(self, data: value_objects.Data) -> value_objects.Data:
        self.register(data)

        yield from self.get_data(
            self.connection.query(f"SELECT * FROM {self.view_name};")  # noqa: S608
        )


# Domain > Domain Services
def test_compress_to_gzip(fake_gzip: bytes) -> None:
    assert domain_services.compress_to_gzip(*(TEST_DATA_FOR_GZIP,)) == fake_gzip


def test_decompress_from_gzip(fake_gzip: bytes) -> None:
    assert (
        domain_services.decompress_from_gzip(
            fake_gzip,
        )
        == TEST_DATA_FOR_GZIP_BYTES
    )


# Adapters > Ports > DuckDB
def test_tranform_duckdb() -> None:
    conn: DuckDBPyConnection = connect()
    data: tuple[dict, ...] = (dict(a=1),)

    assert (
        tuple(FakeTransformDuckDB(conn, "test_table", 5, as_iterator=True)(data))
        == data
    )


# Unit of Work > Data > Path
@pytest.mark.asyncio
async def test_path_data_unit_of_work() -> None:
    with (
        NamedTemporaryFile(mode="w+", suffix=".txt") as temp_file,
        pathlib.PathDataUnitOfWork()(
            destination=PathDestination(temp_file.name),
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
