#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 1 March 2026

from typing import TYPE_CHECKING

from pydantic import validate_call
from sqlalchemy.dialects.postgresql import insert as insert_postgres
from sqlalchemy.dialects.sqlite import insert as insert_sqlite

from ...adapters.utils.database.sqlmodel import AbstractSQLModel
from ...domain import value_objects
from . import AbstractDataPort

if TYPE_CHECKING:
    from sqlalchemy import Engine


class SQLModelDataAdapter(AbstractSQLModel, AbstractDataPort):
    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    def extract(
        self,
        *,
        source: value_objects.SQLModelSource,
    ) -> value_objects.Data:
        return self.session.execute(source.query).mappings()

    @validate_call(config=value_objects.CONFIG_DICT, validate_return=True)
    async def load(
        self,
        data: value_objects.Data,
        *,
        destination: value_objects.SQLModelDestination,
    ) -> value_objects.ResourceLocation:
        engine: Engine = self.session.get_bind()

        self.session.exec(
            (
                insert_postgres
                if engine.dialect.name == value_objects.DbDialect.postgresql
                else insert_sqlite
            )(table=destination.model)
            .values(tuple(data))
            .on_conflict_do_nothing(
                index_elements=destination.model.__table__.primary_key.columns,
            )
        )

        return value_objects.Table(
            destination.model.__tablename__,
            destination.model.__table__.schema or value_objects.DEFAULT_SCHEMA,
        )
