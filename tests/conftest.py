#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 2 March 2026

from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import pytest_asyncio
from pydantic import AnyUrl, validate_call

from voxrow.core.domain import domain_services, value_objects
from voxrow.core.services.handlers import etl
from voxrow.core.services.unit_of_work import pathlib
from voxrow.web.domain.value_objects import Database, OAuthCreds, Settings

# Constants
TEST_FILES_DIR: Path = Path("tests") / "files"
TEST_DATALAKE_DIR: Path = TEST_FILES_DIR / "datalake" / "raw"
TEST_KEY: str = "123"
TEST_DATE: str = "2026-01-19"


@lru_cache
@validate_call
def fake_get_settings(tmp_path: Path) -> Settings:
    return Settings(
        bps_key=TEST_KEY,
        cloudflare_r2=value_objects.Boto3Credential(
            endpoint_url=f"https://{TEST_KEY}.r2.cloudflarestorage.com",
            aws_access_key_id=TEST_KEY,
            aws_secret_access_key=TEST_KEY,
        ),
        cron_secret=TEST_KEY,
        database=Database(
            datawarehouse_silver=AnyUrl(f"sqlite:///{tmp_path}/db.dwh-silver.sqlite3"),
            main=AnyUrl(f"sqlite:///{tmp_path}/db.main.sqlite3"),
        ),
        decodo_web_scraping_token=TEST_KEY,
        google=OAuthCreds(
            client_id=TEST_KEY,
            client_secret=TEST_KEY,
        ),
    )


@pytest.fixture
def fake_raw_stock_summary_value() -> str:
    return (TEST_DATALAKE_DIR / "idx.co.id" / "GetStockSummary.json").read_text()


@pytest_asyncio.fixture
async def fake_raw_stock_summary_output(
    fake_raw_stock_summary_value: str,
) -> value_objects.Data:
    uow: pathlib.PathDataUnitOfWork = pathlib.PathDataUnitOfWork()

    with NamedTemporaryFile(mode="w+b", suffix=".json.gz") as tmp_file:
        # Fake Cloudflare R2 file
        yield {
            await etl(
                source=fake_raw_stock_summary_value,
                destination=uow(
                    destination=value_objects.PathDestination(
                        file=tmp_file.name,
                        is_bytes=True,
                    ),
                ),
                transform=domain_services.compress_to_gzip,
            ): domain_services.loads_from_json(fake_raw_stock_summary_value),
        }
