#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 January 2026

import logging
from collections.abc import Callable
from io import BytesIO
from typing import ClassVar
from unittest.mock import MagicMock

import pandas as pd
import pytest
from anyio import Path
from duckdb import DuckDBPyConnection
from google.cloud.bigquery import Client as BigqueryClient
from google.oauth2.service_account import Credentials
from obs import ObsClient
from pandas.testing import assert_frame_equal
from pydantic import (
    AnyUrl,
    BaseModel,
    DirectoryPath,
    FilePath,
    HttpUrl,
    SecretStr,
    validate_call,
)
from pydantic.dataclasses import dataclass
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, MetaData, Session, select, text

from voxrow.core.adapters.data.cryptography import AesGcmEncryptionDataAdapter
from voxrow.core.adapters.utils.database.bigquery import (
    get_client as bigquery_get_client,
)
from voxrow.core.adapters.utils.database.duckdb import AbstractDuckDB
from voxrow.core.adapters.utils.database.sqlmodel import PydanticJSON, SQLModelEntity
from voxrow.core.adapters.utils.storage.obs import (
    get_client as obs_get_client,
)
from voxrow.core.domain import domain_services, value_objects
from voxrow.core.services import handlers
from voxrow.core.services.unit_of_work import (
    bigquery,
    boto3,
    cryptography,
    duckdb,
    httpx,
    obs,
    pathlib,
    sqlmodel,
)


# Mocks
@pytest.fixture
def mock_bigquery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "voxrow.core.adapters.utils.database.bigquery.Client",
        lambda *args, **kwargs: MagicMock(  # noqa: ARG005
            spec=BigqueryClient,
            load_table_from_json=MagicMock(return_value=MagicMock(output_rows=1)),
            query=MagicMock(
                return_value=MagicMock(
                    result=MagicMock(
                        return_value=(dict(a=1),),
                    ),
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        "voxrow.core.adapters.utils.database.bigquery.Credentials.from_service_account_file",
        lambda *args, **kwargs: MagicMock(spec=Credentials),  # noqa: ARG005
    )


@pytest.fixture
def mock_httpx(test_files_dir: DirectoryPath, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "voxrow.core.adapters.data.httpx.get",
        lambda *args, **kwargs: MagicMock(  # noqa: ARG005
            json=MagicMock(
                return_value=domain_services.loads_from_json(
                    (
                        test_files_dir / "jsonplaceholder" / "users" / "get.json"
                    ).read_text()
                ),
            ),
        ),
    )


@pytest.fixture
def fake_pandas_dataframe() -> pd.DataFrame:
    return pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [25, 30]})


@pytest.fixture
def fake_parquet_bytes(fake_pandas_dataframe: pd.DataFrame) -> BytesIO:
    buffer: BytesIO = BytesIO()

    fake_pandas_dataframe.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    yield buffer

    buffer.close()


@pytest.fixture
def mock_obs(
    fake_message: str,
    fake_parquet_bytes: BytesIO,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "voxrow.core.adapters.utils.storage.obs.ObsClient",
        lambda *args, **kwargs: MagicMock(  # noqa: ARG005
            spec=ObsClient,
            completeMultipartUpload=MagicMock(
                **{"return_value.status": 200},
            ),
            getObject=MagicMock(
                return_value=MagicMock(
                    status=200,
                    **{
                        "body.response.read.side_effect": (
                            fake_message.encode(),
                            None,
                            fake_parquet_bytes.read(),
                            None,
                        ),
                    },
                ),
            ),
            initiateMultipartUpload=MagicMock(
                **{"return_value.status": 200},
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
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def __call__(self, data: value_objects.Data) -> value_objects.Data:
        self.register(data)

        yield from self.get_data(
            self.connection.query(f"SELECT a * 2 AS b FROM {self.view_name};")  # noqa: S608
        )


class TestHandlersEtl:
    @pytest.mark.asyncio
    async def test_aes_gcm_encryption(self, tmp_path: DirectoryPath) -> None:
        uow: cryptography.AesGcmEncryptionDataUnitOfWork = (
            cryptography.AesGcmEncryptionDataUnitOfWork(
                AesGcmEncryptionDataAdapter.generate_key()
            )
        )
        destination_file: FilePath = tmp_path / "destination.enc"
        source_file: FilePath = tmp_path / "source.txt"
        content: bytes = b"Hello world!"

        source_file.write_bytes(content)

        await handlers.etl(
            source=source_file.open("rb"),
            destination=uow(
                destination=value_objects.EncryptionDestination(
                    destination_file.open("wb")
                )
            ),
        )

        with uow(
            source=value_objects.EncryptionSource(destination_file.open("rb")),
        ):
            assert uow.data.extract(source=uow.source).read() == content

    @pytest.mark.asyncio
    async def test_bigquery(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_google_project_id: str,
        fake_google_service_account_file: FilePath,
        mock_bigquery: Callable,  # noqa: ARG002
    ) -> None:
        caplog.set_level(logging.INFO)

        uow: bigquery.BigqueryDataUnitOfWork = bigquery.BigqueryDataUnitOfWork(
            bigquery_get_client(
                fake_google_project_id,
                fake_google_service_account_file,
            )
        )
        fake_dataset: str = "dataset"
        fake_table: str = "table"

        with uow(source=value_objects.BigquerySource("SELECT 1 a;")):
            result: tuple = tuple(uow.data.extract(source=uow.source))

            assert result == (dict(a=1),)

        await handlers.etl(
            source=result,
            destination=uow(
                destination=value_objects.BigqueryDestination(
                    fake_google_project_id,
                    fake_dataset,
                    fake_table,
                    schema=[value_objects.BigqquerySchemaField("a", "INTEGER")],
                ),
            ),
        )

        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO
        assert (
            caplog.records[0].message
            == f"Loaded into Google BigQuery '{fake_google_project_id}.{fake_dataset}.{fake_table}': 1 row"  # noqa: E501
        )

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

    @pytest.mark.filterwarnings(
        "ignore:ssl.PROTOCOL_TLS is deprecated:DeprecationWarning"
    )
    @pytest.mark.filterwarnings(
        "ignore:datetime.datetime.utcnow\\(\\):DeprecationWarning:obs.client"
    )
    @pytest.mark.asyncio
    async def test_obs(
        self,
        fake_message: str,
        fake_pandas_dataframe: pd.DataFrame,
        tmp_path: DirectoryPath,
        mock_obs: Callable,  # noqa: ARG002
    ) -> None:
        uow: obs.ObsDataUnitOfWork = obs.ObsDataUnitOfWork(
            obs_get_client(
                SecretStr("AccessKeyID"),
                SecretStr("SecretAccessKey"),
                HttpUrl("https://obs.ap-southeast-1.myhuaweicloud.com"),
            )
        )
        bucket_name: str = "examplebucket"

        with (
            uow(
                source=value_objects.ObsSource(
                    bucket_name,
                    "file.txt",
                    value_objects.ContentType.text,
                ),
            ),
            BytesIO() as value,
        ):
            data: value_objects.Data = uow.data.extract(source=uow.source)

            while True:
                chunk: any | None = data.read()

                if not chunk:
                    break

                value.write(chunk)

            data.close()
            value.seek(0)

            assert value.read().decode(value_objects.ENCODING) == fake_message

        with (
            uow(
                source=value_objects.ObsSource(
                    bucket_name,
                    "file.parquet",
                    value_objects.ContentType.parquet,
                ),
            ),
            BytesIO() as value,
        ):
            data: value_objects.Data = uow.data.extract(source=uow.source)

            while True:
                chunk: any | None = data.read()

                if not chunk:
                    break

                value.write(chunk)

            data.close()
            value.seek(0)
            assert_frame_equal(
                fake_pandas_dataframe,
                pd.read_parquet(value),
            )

        object_key: str = "file.mp4"
        fake_file: FilePath = tmp_path / object_key

        fake_file.write_bytes(fake_message.encode())

        assert await handlers.etl(
            source=fake_file.open(mode="rb"),
            destination=uow(
                destination=value_objects.ObsDestination(
                    bucket_name,
                    object_key,
                    value_objects.ContentType.mp4,
                ),
            ),
        ) == AnyUrl(f"{value_objects.Boto3Scheme.obs}://{bucket_name}/{object_key}")

    @pytest.mark.asyncio
    async def test_pathlib(self, fake_message: str, tmp_path: DirectoryPath) -> None:
        data_bytes: bytes = fake_message.encode()
        uow: pathlib.PathDataUnitOfWork = pathlib.PathDataUnitOfWork()

        with (tmp_path / "file.txt").open(mode="w+") as temp_file:
            file: Path = await handlers.etl(
                source=fake_message,
                destination=uow(
                    destination=value_objects.PathDestination(temp_file.name)
                ),
            )

            assert file == Path(temp_file.name)
            assert file.read_text() == fake_message

        with (tmp_path / "file.dat").open(mode="wb+") as temp_file:
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
