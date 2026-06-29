#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 5 May 2026

import gzip
from datetime import date

import pytest

from voxrow.core.domain import domain_services
from voxrow.core.domain.value_objects import ENCODING, CaseInsensitiveStrEnum

# Constants
TEST_DATA: tuple = (1, 2, 3)
TEST_DATA_BYTES: bytes = str(TEST_DATA).encode(ENCODING)
TEST_DATA_JSON: str = "[1, 2, 3]"


@pytest.fixture
def fake_gzip() -> bytes:
    return gzip.compress(TEST_DATA_BYTES, compresslevel=9)


class TestDomainServices:
    def test_functions(self) -> None:
        assert isinstance(domain_services.today(), date)
        assert domain_services.now().tzinfo is not None

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
    def test_case_insentive_str_enum(self) -> None:
        class FakeEnum(CaseInsensitiveStrEnum):
            A = "a"

        FakeEnum("A")

        with pytest.raises(
            ValueError,
            match="'b' is not a valid "
            r"TestValueObjects.test_case_insentive_str_enum.<locals>.FakeEnum",
        ):
            FakeEnum("b")
