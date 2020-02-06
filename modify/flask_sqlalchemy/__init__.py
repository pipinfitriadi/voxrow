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
from ... import to_json

try:
    from ....config import SCHEMA
except Exception:
    SCHEMA = 'VOXROW'


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

    def __query(self, string, **kwargs):
        '''
        Optional kwargs can be use for best query result.
        1. bind_key: str
           - Use it if we have more than one database in one system.
        2. json_mode: bool
           - Use json_mode=True if we want result as string dumps json.
        '''

        args = []

        for key in (
            _kwargs := dict(
                filter(
                    lambda kwarg: kwarg[0] not in [
                        'bind_key',
                        'json_mode'
                    ],
                    kwargs.items()
                )
            )
        ):
            for parameter_type, database_column_type in [
                [int, Integer],
                [float, Float],
                [datetime, DateTime],
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

        try:
            query_result = session.execute(
                text(string).bindparams(*args, **_kwargs)
            )

            # memory-efficient built-in SqlAlchemy iterator /
            # generator:
            # https://stackoverflow.com/questions/7389759/memory-efficient-built-in-sqlalchemy-iterator-generator
            # Python: Using Flask to stream chunked dynamic content to end
            # users
            # https://fabianlee.org/2019/11/18/python-using-flask-to-stream-chunked-dynamic-content-to-end-users/
            # Streaming Contents
            # https://flask.palletsprojects.com/en/1.1.x/patterns/streaming/#basic-usage
            # Streaming JSON with Flask
            # https://blog.al4.co.nz/2016/01/streaming-json-with-flask/
            if (json_mode := kwargs.get('json_mode') is True):
                yield '['

            while True:
                batch = query_result.fetchmany(100_000)

                if not batch:
                    break

                rows = batch.__iter__()

                try:
                    prev_row = next(rows)

                    def to_result(row, json_mode=False):
                        data = dict(
                            column for column in row.items()
                        )
                        return (
                            to_json(data)
                            if json_mode else data
                        )

                    for row in rows:
                        result = to_result(prev_row, json_mode)
                        prev_row = row
                        yield result + ', ' if json_mode else result

                    yield to_result(prev_row, json_mode)
                except StopIteration:
                    pass

            if json_mode:
                yield ']'

            query_result.close()
            session.commit()
        except Exception:
            session.rollback()

            if current_app.debug:
                raise
        finally:
            session.close()

    def query(self, string, **kwargs):
        '''
        Optional kwargs can be use for best query result.
        1. bind_key: str
           - Use it if we have more than one database in one system.
        2. json_mode: bool
           - Use json_mode=True if we want result as string dumps json.
        3. generator_mode: bool
           - Use generator_mode=True if we want result as generator.
        '''

        # Issue with a python function returning a generator or a normal object
        # https://stackoverflow.com/questions/25313283/issue-with-a-python-function-returning-a-generator-or-a-normal-object
        generator_mode = kwargs.pop('generator_mode', None)
        result = self.__query(string, **kwargs)

        if not generator_mode:
            result = (
                ''.join(result)
                if kwargs.get('json_mode') is True
                else list(result)
            )

        return result
