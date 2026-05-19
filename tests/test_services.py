#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 January 2026

from collections.abc import Callable
from tempfile import NamedTemporaryFile
from typing import ClassVar
from unittest.mock import MagicMock

import pytest
from anyio import Path
from duckdb import DuckDBPyConnection
from google.cloud.bigquery import Client
from google.oauth2.service_account import Credentials
from pydantic import AnyUrl, BaseModel, validate_call
from pydantic.dataclasses import dataclass
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, MetaData, Session, select, text

from voxrow.core.adapters.database.bigquery import get_client
from voxrow.core.adapters.database.sqlmodel import PydanticJSON, SQLModelEntity
from voxrow.core.adapters.ports.duckdb import AbstractDuckDB
from voxrow.core.domain import domain_services, value_objects
from voxrow.core.services import handlers
from voxrow.core.services.unit_of_work import (
    bigquery,
    boto3,
    duckdb,
    httpx,
    pathlib,
    sqlmodel,
)

from .conftest import TEST_FILES_DIR


# Mocks
@pytest.fixture
def mock_bigquery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "voxrow.core.adapters.database.bigquery.Client",
        lambda *args, **kwargs: MagicMock(  # noqa: ARG005
            spec=Client,
            query=MagicMock(
                return_value=MagicMock(
                    result=MagicMock(
                        return_value=MagicMock(
                            pages=((dict(a=1),),),
                        )
                    ),
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        "voxrow.core.adapters.database.bigquery.Credentials.from_service_account_file",
        lambda *args, **kwargs: MagicMock(spec=Credentials),  # noqa: ARG005
    )


@pytest.fixture
def mock_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "voxrow.core.adapters.ports.httpx.get",
        lambda *args, **kwargs: MagicMock(  # noqa: ARG005
            json=MagicMock(
                return_value=domain_services.loads_from_json(
                    (
                        TEST_FILES_DIR / "jsonplaceholder" / "users" / "get.json"
                    ).read_text()
                ),
            ),
        ),
    )


class FakeSQLModel(SQLModelEntity):
    metadata: ClassVar[MetaData] = MetaData()


class FakeJsonColumn(BaseModel):
    c: str


class FakeTable(FakeSQLModel, table=True):
    a: int
    b: FakeJsonColumn = Field(
        sa_type=PydanticJSON(FakeJsonColumn).with_variant(
            JSONB,
            value_objects.DbDialect.postgresql,
        )
    )
    __tablename__: str = "fake_table"


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class FakeTransformDuckDB(AbstractDuckDB):
    @validate_call
    def __call__(self, data: value_objects.Data) -> value_objects.Data:
        self.register(data)

        yield from self.get_data(
            self.connection.query(f"SELECT a * 2 AS b FROM {self.view_name};")  # noqa: S608
        )


class TestHandlersEtl:
    @pytest.mark.asyncio
    async def test_bigquery(self, mock_bigquery: Callable) -> None:  # noqa: ARG002
        uow: bigquery.BigqueryDataUnitOfWork = bigquery.BigqueryDataUnitOfWork(
            get_client(
                "project-id",
                TEST_FILES_DIR / "google" / "service_account.json",
            )
        )

        with uow(source=value_objects.BigquerySource("SELECT 1 a;")):
            assert tuple(uow.data.extract(source=uow.source)) == (dict(a=1),)

    @pytest.mark.asyncio
    async def test_boto3(
        self,
        fake_bucket: str,
        fake_boto3_credential: value_objects.Boto3Credential,
        mock_boto3: Callable,  # noqa: ARG002
    ) -> None:
        key: str = "fake_file_new.json"
        uow: boto3.Boto3DataUnitOfWork = boto3.Boto3DataUnitOfWork(
            fake_boto3_credential,
            value_objects.Boto3Scheme.r2,
        )

        assert await handlers.etl(
            source=uow(
                source=value_objects.Boto3Source(fake_bucket, "fake_file_old.json"),
            ),
            destination=uow(
                destination=value_objects.Boto3Destination(
                    fake_bucket,
                    key,
                    value_objects.ContentType.json,
                ),
            ),
        ) == AnyUrl(f"{value_objects.Boto3Scheme.r2}://{fake_bucket}/{key}")

    def test_httpx(self, mock_httpx: Callable) -> None:  # noqa: ARG002
        fake_user_total: int = 10

        with httpx.HttpxDataUnitOfWork()(
            source=value_objects.HttpxSource(
                "https://jsonplaceholder.typicode.com/users"
            ),
        ) as uow:
            assert len(uow.data.extract(source=uow.source)) == fake_user_total

    @pytest.mark.asyncio
    async def test_pathlib(self) -> None:
        data: str = "Test"
        data_bytes: bytes = data.encode()
        uow: pathlib.PathDataUnitOfWork = pathlib.PathDataUnitOfWork()

        with NamedTemporaryFile(mode="w+", suffix=".txt") as temp_file:
            file: Path = await handlers.etl(
                source=data,
                destination=uow(
                    destination=value_objects.PathDestination(temp_file.name)
                ),
            )

            assert file == Path(temp_file.name)
            assert file.read_text() == data

        with NamedTemporaryFile(mode="wb+", suffix=".dat") as temp_file:
            file: Path = await handlers.etl(
                source=data_bytes,
                destination=uow(
                    destination=value_objects.PathDestination(
                        temp_file.name,
                        is_bytes=True,
                    ),
                ),
            )

            assert file == Path(temp_file.name)

            with uow(
                source=value_objects.PathSource(
                    file,
                    is_bytes=True,
                ),
            ):
                assert uow.data.extract(source=uow.source) == data_bytes

        with (
            pytest.raises(
                ValueError,
                match="destination or source must not be empty",
            ),
            uow(),
        ):
            pass  # pragma: no cover

    @pytest.mark.asyncio
    async def test_duckdb(self, fake_duckdb_conn: DuckDBPyConnection) -> None:
        data: tuple[dict, ...] = (dict(b=2),)
        destination_table: str = "destination"
        uow: duckdb.DuckDBDataUnitOfWork = duckdb.DuckDBDataUnitOfWork(
            fake_duckdb_conn,
            as_iterator=True,
        )
        table: value_objects.Table = await handlers.etl(
            source=fake_duckdb_conn.query("SELECT 1 a;"),
            destination=uow(
                destination=value_objects.DuckDBDestination(
                    f"""
                    CREATE TABLE
                        {destination_table}
                    AS
                    SELECT
                        *
                    FROM
                        source
                    ;
                    """,  # noqa: S608
                    table=value_objects.Table(
                        destination_table,
                        "main",
                    ),
                ),
            ),
            transform=FakeTransformDuckDB(
                fake_duckdb_conn,
                "fake_table",
                fetch_size=5,
                as_iterator=True,
            ),
        )

        with uow(
            source=value_objects.DuckDBSource(
                f"SELECT * FROM {table.schema}.{table.name};",  # noqa: S608
            ),
        ):
            assert tuple(uow.data.extract(source=uow.source)) == data

    @pytest.mark.asyncio
    async def test_sqlmodel(self, fake_db_engine: Engine) -> None:
        fake_json_column: FakeJsonColumn = FakeJsonColumn(c="tes")

        FakeSQLModel.metadata.create_all(fake_db_engine)

        with Session(fake_db_engine) as session:
            uow: sqlmodel.SQLModelDataUnitOfWork = sqlmodel.SQLModelDataUnitOfWork(
                session
            )

            await handlers.etl(
                source=uow(source=value_objects.SQLModelSource(text("SELECT 1 AS a;"))),
                destination=uow(
                    destination=value_objects.SQLModelDestination(FakeTable)
                ),
                transform=lambda data: ({**row, "b": fake_json_column} for row in data),
            )

            fake_row: FakeTable = session.exec(
                select(FakeTable).where(FakeTable.a == 1)
            ).first()

            fake_row.delete()

        assert fake_row.a == 1
        assert fake_row.b.c == fake_json_column.c
        assert fake_row.deleted_at is not None
