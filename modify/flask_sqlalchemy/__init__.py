#!/usr/bin/env python3

# Copyright 2020 Pipin Fitriadi <pipinfitriadi@gmail.com>

# Licensed under the Microsoft Reference Source License (MS-RSL)

# This license governs use of the accompanying software. If you use the
# software, you accept this license. If you do not accept the license, do not
# use the software.

# 1. Definitions

# The terms "reproduce," "reproduction" and "distribution" have the same
# meaning here as under U.S. copyright law.

# "You" means the licensee of the software.

# "Your company" means the company you worked for when you downloaded the
# software.

# "Reference use" means use of the software within your company as a reference,
# in read only form, for the sole purposes of debugging your products,
# maintaining your products, or enhancing the interoperability of your
# products with the software, and specifically excludes the right to
# distribute the software outside of your company.

# "Licensed patents" means any Licensor patent claims which read directly on
# the software as distributed by the Licensor under this license.

# 2. Grant of Rights

# (A) Copyright Grant- Subject to the terms of this license, the Licensor
# grants you a non-transferable, non-exclusive, worldwide, royalty-free
# copyright license to reproduce the software for reference use.

# (B) Patent Grant- Subject to the terms of this license, the Licensor grants
# you a non-transferable, non-exclusive, worldwide, royalty-free patent
# license under licensed patents for reference use.

# 3. Limitations

# (A) No Trademark License- This license does not grant you any rights to use
# the Licensor's name, logo, or trademarks.

# (B) If you begin patent litigation against the Licensor over patents that
# you think may apply to the software (including a cross-claim or counterclaim
# in a lawsuit), your license to the software ends automatically.

# (C) The software is licensed "as-is." You bear the risk of using it. The
# Licensor gives no express warranties, guarantees or conditions. You may have
# additional consumer rights under your local laws which this license cannot
# change. To the extent permitted under your local laws, the Licensor excludes
# the implied warranties of merchantability, fitness for a particular purpose
# and non-infringement.

from datetime import date, datetime

from flask import current_app
from flask_sqlalchemy import BaseQuery, SQLAlchemy as _SQLAlchemy
from sqlalchemy import bindparam
from sqlalchemy.sql import text
from sqlalchemy.types import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Float,
    JSON,
    String
)

from .model import Model


class SQLAlchemy(_SQLAlchemy):
    def __init__(
        self,
        app=None,
        use_native_unicode=True,
        session_options=None,
        metadata=None,
        query_class=BaseQuery,
        model_class=Model,
        engine_options=None
    ):
        super().__init__(
            app=app,
            use_native_unicode=use_native_unicode,
            session_options=session_options,
            metadata=metadata,
            query_class=query_class,
            model_class=model_class,
            engine_options=engine_options
        )
        self.Model.db = self

    def query(self, string, **kwargs):
        '''
        Optional kwargs can be use for best query result.
        1. bind_key: str
           - Use if we have more than one database in one system.
        '''

        args = []

        for key in (
            _kwargs := dict(
                filter(
                    lambda kwarg: kwarg[0] not in [
                        'bind_key',
                        'stream_results'
                    ],
                    kwargs.items()
                )
            )
        ):
            for parameter_type, database_column_type in [
                [int, Integer],
                [float, Float],
                [date, Date],
                [dict, JSON],
                [bool, Boolean],
                [type(None), None]
            ]:
                if isinstance(_kwargs[key], parameter_type):
                    parameter = bindparam(
                        key=key,
                        type_=database_column_type
                    )
                    break
            else:
                parameter = bindparam(
                    key=key,
                    type_=String
                )

            args.append(parameter)

        bind_key = kwargs.get('bind_key')
        session = self.create_session({
            'bind': self.get_engine(
                *(
                    (current_app, bind_key)
                    if isinstance(bind_key, str)
                    else (current_app,)
                )
            ).execution_options(stream_results=True)
        })()
        data = []

        try:
            query_result = session.execute(
                text(string).bindparams(*args, **_kwargs)
            )

            # memory-efficient built-in SqlAlchemy iterator/generator:
            # https://stackoverflow.com/questions/7389759/memory-efficient-built-in-sqlalchemy-iterator-generator
            while True:
                batch = query_result.fetchmany(100_000)

                if not batch:
                    break

                data.extend(
                    dict(
                        column for column in row.items()
                    ) for row in batch
                )

            query_result.close()
            session.commit()
        except Exception:
            session.rollback()

            if current_app.debug:
                raise
        finally:
            session.close()

        return data
