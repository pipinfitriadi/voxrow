#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 5 May 2026

import gzip

import pytest

from voxrow.core.domain import domain_services
from voxrow.core.domain.value_objects import ENCODING

# Constants
TEST_DATA_FOR_GZIP: tuple = (1, 2, 3)
TEST_DATA_FOR_GZIP_BYTES: bytes = str(TEST_DATA_FOR_GZIP).encode(ENCODING)


@pytest.fixture
def fake_gzip() -> bytes:
    return gzip.compress(TEST_DATA_FOR_GZIP_BYTES, compresslevel=9)


class TestDomainServices:
    def test_compress_to_gzip(self, fake_gzip: bytes) -> None:
        assert domain_services.compress_to_gzip(*(TEST_DATA_FOR_GZIP,)) == fake_gzip

    def test_decompress_from_gzip(self, fake_gzip: bytes) -> None:
        assert (
            domain_services.decompress_from_gzip(
                fake_gzip,
            )
            == TEST_DATA_FOR_GZIP_BYTES
        )
