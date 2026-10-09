#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 5 May 2026

import gzip
from datetime import date

import pytest
from pydantic import DirectoryPath, FilePath, TypeAdapter, ValidationError

from voxrow.core.domain import domain_services, value_objects

# Constants
TEST_DATA: tuple = (1, 2, 3)
TEST_DATA_BYTES: bytes = str(TEST_DATA).encode(value_objects.ENCODING)
TEST_DATA_JSON: str = "[1, 2, 3]"


@pytest.fixture
def fake_gzip() -> bytes:
    return gzip.compress(TEST_DATA_BYTES, compresslevel=9)


class TestDomainServices:
    def test_functions(self) -> None:
        assert isinstance(domain_services.today(), date)
        assert domain_services.now().tzinfo is not None

    def test_csv(
        self,
        test_files_dir: DirectoryPath,
        fake_data: value_objects.Data,
    ) -> None:
        csv_with_header: FilePath = test_files_dir / "with-header.csv"
        csv_without_header: FilePath = test_files_dir / "without-header.csv"
        delimiter: str = "SEMICOLON"
        has_header: bool = False

        # Dumps
        assert (
            domain_services.DumpsToCsv()(fake_data).getvalue()
            == csv_with_header.read_text()
        )
        assert (
            domain_services.DumpsToCsv(
                delimiter=delimiter,
                has_header=has_header,
            )(fake_data).getvalue()
            == csv_without_header.read_text()
        )

        # Loads
        assert tuple(domain_services.LoadsToCsv()(csv_with_header.open())) == fake_data
        assert tuple(
            domain_services.LoadsToCsv(
                delimiter=delimiter,
                has_header=has_header,
            )(csv_without_header.open())
        ) == tuple(list(row.values()) for row in fake_data)

    def test_gzip(self, fake_gzip: bytes) -> None:
        assert domain_services.compress_to_gzip(*(TEST_DATA,)) == fake_gzip
        assert (
            domain_services.decompress_from_gzip(
                fake_gzip,
            )
            == TEST_DATA_BYTES
        )

    def test_json(self) -> None:
        assert domain_services.dumps_to_json(*(TEST_DATA,)) == TEST_DATA_JSON
        assert tuple(domain_services.loads_from_json(TEST_DATA_JSON)) == TEST_DATA


class TestValueObjects:
    @pytest.fixture(scope="class", autouse=True)
    def host(self) -> TypeAdapter:
        return TypeAdapter(value_objects.Host)

    def test_case_insentive_str_enum(self) -> None:
        class FakeEnum(value_objects.CaseInsensitiveStrEnum):
            A = "a"

        FakeEnum("A")

        with pytest.raises(
            ValueError,
            match="'b' is not a valid "
            r"TestValueObjects.test_case_insentive_str_enum.<locals>.FakeEnum",
        ):
            FakeEnum("b")

    @pytest.mark.parametrize(
        "value",
        [
            "127.0.0.1",
            "2001:db8::1",
            "example.com",
            "localhost",
        ],
    )
    def test_host_valid(self, host: TypeAdapter, value: str) -> None:
        assert str(host.validate_python(value)) == value.lower()

    @pytest.mark.parametrize(
        "value",
        [
            "example..com",
            "-leading-dash.com",
            "invalid_ip.34.2.1",
        ],
    )
    def test_host_invalid(self, host: TypeAdapter, value: str) -> None:
        with pytest.raises(ValidationError):
            host.validate_python(value)
