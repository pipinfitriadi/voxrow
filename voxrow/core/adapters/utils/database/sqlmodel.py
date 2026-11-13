#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 1 March 2026

from datetime import datetime
from typing import Any, TypeAlias

from pydantic import TypeAdapter, validate_call
from pydantic.dataclasses import dataclass
from pydantic_core import MultiHostUrl
from sqlalchemy import JSON, Engine, TypeDecorator
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.schema import CreateSchema
from sqlalchemy.sql.type_api import _T
from sqlmodel import DateTime, Field, Session, SQLModel, create_engine

from ....domain import domain_services, entity, value_objects


@dataclass(config=value_objects.CONFIG_DICT, frozen=True)
class AbstractSQLModel:
    session: Session


class SQLModelDomain(value_objects.Domain, SQLModel):
    pass


class SQLModelEntity(SQLModelDomain, entity.Entity):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=domain_services.now,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=domain_services.now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs=dict(onupdate=domain_services.now),
    )
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

    def delete(self) -> None:
        self.deleted_at = domain_services.now()


class PydanticJSON(TypeDecorator):
    impl: TypeAlias = JSON  # noqa: PYI042
    cache_ok: bool = True

    def __init__(self, model_cls: type) -> None:
        super().__init__()
        self._adapter = TypeAdapter(model_cls)
        self._model_cls = model_cls

    def process_bind_param(
        self,
        value: _T | None,
        dialect: Dialect,  # noqa: ARG002
    ) -> any:
        # model -> dict.
        return value if value is None or isinstance(value, dict) else value.model_dump()

    def process_result_value(
        self,
        value: Any | None,  # noqa: ANN401
        dialect: Dialect,  # noqa: ARG002
    ) -> _T | None:
        # dict -> instance
        return value if value is None else self._adapter.validate_python(value)


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def get_schema(engine: Engine, schema: str = value_objects.DEFAULT_SCHEMA) -> str:
    if engine.dialect.name == value_objects.DbDialect.postgresql:  # pragma: no cover
        with engine.begin() as conn:
            conn.execute(CreateSchema(schema, if_not_exists=True))
    else:
        schema = value_objects.DEFAULT_SCHEMA

    return schema


@validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
def get_db_engine(db_dsn: value_objects.DatabaseType) -> Engine:
    return create_engine(
        str(db_dsn),
        **(
            dict(connect_args=dict(check_same_thread=False))
            if "sqlite" in db_dsn.scheme.lower()
            else {}
        ),
    )


@validate_call(validate_return=True)
def database_without_password(
    db_dsn: value_objects.DatabaseType,
) -> value_objects.DatabaseType:
    base_url: MultiHostUrl = MultiHostUrl(str(db_dsn))

    return db_dsn.__class__(
        str(
            MultiHostUrl.build(
                scheme=base_url.scheme,
                hosts=[
                    {key: value for key, value in host.items() if key != "password"}
                    for host in base_url.hosts()
                ],
                path=base_url.path.lstrip("/"),
                query=base_url.query,
                fragment=base_url.fragment,
            )
        )
    )
