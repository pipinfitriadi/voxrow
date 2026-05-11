#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 January 2026

from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, ClassVar

import pytest
from anyio import Path
from duckdb import DuckDBPyConnection, connect
from pydantic import AnyUrl, BaseModel, validate_call
from pydantic.dataclasses import dataclass
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, MetaData, Session, select, text

from voxrow.core.adapters.database.sqlmodel import (
    PydanticJSON,
    SQLModelEntity,
    get_db_engine,
    get_schema,
)
from voxrow.core.adapters.ports.duckdb import AbstractDuckDB
from voxrow.core.domain import value_objects
from voxrow.core.services import handlers
from voxrow.core.services.unit_of_work import duckdb, pathlib, sqlmodel

if TYPE_CHECKING:
    from sqlalchemy import Engine


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


class TestHandlers:
    @pytest.mark.asyncio
    async def test_etl_pathlib(self) -> None:
        data: str = "Test"
        data_bytes: bytes = data.encode()
        uow: pathlib.PathDataUnitOfWork = pathlib.PathDataUnitOfWork()

        with NamedTemporaryFile(mode="w+", suffix=".txt") as temp_file:
            file: Path = await handlers.etl(
                source=data,
                destination=uow(destination=value_objects.PathDestination(temp_file.name)),
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
            assert uow.data.extract(
                source=value_objects.PathSource(
                    file,
                    is_bytes=True,
                ),
            ) == data_bytes

        with (
            pytest.raises(
                ValueError,
                match="destination or source must not be empty",
            ),
            uow(),
        ):
            pass  # pragma: no cover

    @pytest.mark.asyncio
    async def test_etl_duckdb(self) -> None:
        data: tuple[dict, ...] = (dict(b=2),)
        connection: DuckDBPyConnection = connect()
        destination_table: str = "destination"
        uow: duckdb.DuckDBDataUnitOfWork = duckdb.DuckDBDataUnitOfWork(
            connection,
            as_iterator=True,
        )
        table: value_objects.Table = await handlers.etl(
            source=connection.query("SELECT 1 a;"),
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
                connection,
                "fake_table",
                fetch_size=5,
                as_iterator=True,
            )
        )

        assert (
            tuple(
                uow.data.extract(
                    source=value_objects.DuckDBSource(
                        f"SELECT * FROM {table.schema}.{table.name};",  # noqa: S608
                    ),
                )
            ) == data
        )

    @pytest.mark.asyncio
    async def test_etl_sqlmodel(self, tmp_path: Path) -> None:
        fake_json_column: FakeJsonColumn = FakeJsonColumn(c="tes")
        engine: Engine = get_db_engine(AnyUrl(f"sqlite:///{tmp_path}/database.sqlite3"))
        schema: str = get_schema(engine)

        assert schema == value_objects.DEFAULT_SCHEMA

        FakeSQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            uow: sqlmodel.SQLModelDataUnitOfWork = sqlmodel.SQLModelDataUnitOfWork(
                session
            )

            await handlers.etl(
                source=uow(source=value_objects.SQLModelSource(text("SELECT 1 AS a;"))),
                destination=uow(destination=value_objects.SQLModelDestination(FakeTable)),
                transform=lambda data: [{**row, "b": fake_json_column} for row in data],
            )

            fake_row: FakeTable = session.exec(
                select(FakeTable).where(FakeTable.a == 1)
            ).first()

            fake_row.delete()

            assert fake_row.a == 1
            assert fake_row.b.c == fake_json_column.c
            assert fake_row.deleted_at is not None
