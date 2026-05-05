#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 1 March 2026

from typing import Self

from pydantic import validate_call
from sqlmodel import Session

from ...adapters.database import sqlmodel
from ...adapters.ports.sqlmodel import SQLModelDataPort
from ...domain import value_objects
from ...services import unit_of_work


# Abstracts
class AbstractSQLModelUnitOfWork(
    sqlmodel.AbstractSQLModel,
    unit_of_work.AbstractUnitOfWork,
):
    @validate_call(config=value_objects.CONFIG_DICT)
    def __init__(self, session: Session) -> None:
        self.session = session

    def __enter__(self) -> Self:
        self.session.begin()

        return super().__enter__()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:  # pragma: no cover
        self.session.rollback()


# Implementation
class SQLModelDataUnitOfWork(
    AbstractSQLModelUnitOfWork,
    unit_of_work.AbstractDataUnitOfWork,
):
    @validate_call(config=value_objects.CONFIG_DICT)
    def __init__(self, session: Session) -> None:
        super().__init__(session)

        self.data = SQLModelDataPort(self.session)
