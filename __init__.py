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

from collections.abc import Iterable
from datetime import date, datetime
from json import dumps, JSONDecoder as _JSONDecoder, loads
from json.decoder import JSONDecodeError, WHITESPACE
from os import getenv
from pathlib import Path
from random import randint
import re
from time import sleep
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sshtunnel import SSHTunnelForwarder
from sqlalchemy import bindparam, create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text
from sqlalchemy.types import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    Integer,
    Float,
    JSON,
    String
)

STRING_DATE_FORMAT = '%Y-%m-%d'
STRING_DATETIME_FORMAT = f'{ STRING_DATE_FORMAT }T%H:%M:%S'


def blueprint_name(file):
    # How to get the filename without the extension from a path in Python?
    # https://stackoverflow.com/questions/678236/how-to-get-the-filename-without-the-extension-from-a-path-in-python
    if (
        name := (
            path := Path(file)
        ).resolve().stem
    ) == '__init__':
        name = path.parent.resolve().stem

    return name


# How to convert string int JSON into real int with json.loads
# https://stackoverflow.com/questions/45068797/how-to-convert-string-int-json-into-real-int-with-json-loads
# How to convert to a Python datetime object with JSON.loads?
# https://stackoverflow.com/questions/8793448/how-to-convert-to-a-python-datetime-object-with-json-loads
def deserialize(object):
    '''
    >>> deserialize('2020-04-28'), deserialize('2020-04-28T15:00:46')
    '''

    if isinstance(object, str):
        try:
            object = loads(object)
        except JSONDecodeError:
            pass

        if isinstance(object, str):
            for regex, str_time_format in [
                [
                    r'^\d{4}-\d{2}-\d{2}$',
                    STRING_DATE_FORMAT
                ],
                [
                    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',
                    STRING_DATETIME_FORMAT
                ]
            ]:
                if re.match(regex, object):
                    is_time = False

                    try:
                        object = datetime.strptime(object, str_time_format)

                        is_time = True
                    except Exception:
                        pass

                    if is_time:
                        break
        else:
            object = deserialize(object)
    elif isinstance(object, dict):
        object = {
            key: deserialize(value)
            for key, value in object.items()
        }
    elif isinstance(object, list):
        object = [
            deserialize(value)
            for value in object
        ]

    return object


class JSONDecoder(_JSONDecoder):
    def decode(self, s, _w=WHITESPACE.match):
        return deserialize(
            super().decode(s, _w)
        )


def serialize(object):
    '''
    >>> from json import dumps
    >>> dumps(object, default=serialize)
    '''

    # How to serialize a datetime object as JSON using Python?
    # https://code-maven.com/serialize-datetime-object-as-json-in-python
    if isinstance(object, datetime):
        object = object.strftime(STRING_DATETIME_FORMAT)
    elif isinstance(object, date):
        object = object.strftime(STRING_DATE_FORMAT)
    elif isinstance(object, set):
        object = list(object)

    return object


def json_serializer(object):
    return dumps(object, default=serialize)


def json_deserializer(object):
    return loads(object, cls=JSONDecoder)


def database_uri(
    db_driver='postgresql',
    db_host='localhost',
    db_port=5432,
    db_name='postgres',
    db_user='',
    db_pass='',
    use_charset_utf8=False
):
    if db_driver == 'mysql' and db_port == 5432:
        db_port = 3306

    uri = (
        (
            f'{ db_driver }://{ db_user }:{ db_pass }@'
            f'{ db_host }:{ db_port }/{ db_name }'
        )
        if db_driver else ''
    )

    # flask sqlalchemy mysql encoding problems
    # https://stackoverflow.com/questions/26577334/flask-sqlalchemy-mysql-encoding-problems
    # SQLAlchemy + MySQL + UTF-8 support - how?
    # https://groups.google.com/forum/#!topic/pylons-discuss/ol2m46kiSYA
    return (
        uri + '?charset=utf8'
        if db_driver == 'mysql'
        and use_charset_utf8
        else uri
    )


def database_uri_from_env(
    db_driver_env='DB_DRIVER',
    db_host_env='DB_HOST',
    db_port_env='DB_PORT',
    db_name_env='DB_NAME',
    db_user_env='DB_USER',
    db_pass_env='DB_PASS',
    use_charset_utf8_env='USE_CHARSET_UTF8',
):
    return database_uri(
        getenv(db_driver_env, 'postgresql'),
        getenv(db_host_env, 'localhost'),
        int(
            getenv(db_port_env, '5432')
        ),
        getenv(db_name_env, 'postgres'),
        getenv(db_user_env, ''),
        getenv(db_pass_env, ''),
        getenv(use_charset_utf8_env, 'FALSE').upper() in ['TRUE', '1']
    )


def query(engine, string, **kwargs):
    '''
    engine:
    - obj: SQLAlchemy's engine instance.
    - str: Build SQLAlchemy's engine from string database uri.
    - dict: Build SQLAlchemy's engine from database_uri's func kwargs and
    SSHTunnelForwarder's func kwarg.

    string: str
    - Use for put raw query sql.

    kwargs: dict
    - Optional kwargs can be use for best query result.
        1. generator_mode: bool
            - Use generator_mode=True if we want result as generator.
        2. json_mode: bool
            - Use json_mode=True if we want result as string dumps json.
        3. debug_mode: bool
            - Use debug_mode=False if you don't want to see error
            information.
        4. fetch_size: int
            - Use for set how many rows use on every fetch.
            - Default value is 100,000.
        5. stream_results: bool
            - Use stream_results=False for update/insert/delete query.
        6. use_charset_utf8: bool
            - Use use_charset_utf8=True for mysql driver if needed.
    '''

    if isinstance(engine, dict):
        database_uri_param = [
            'db_driver',
            'db_host',
            'db_port',
            'db_name',
            'db_user',
            'db_pass',
            'use_charset_utf8'
        ]
        ssh_param = {
            key: value
            for key, value in engine.items()
            if key not in database_uri_param
        }
        engine = {
            key: value
            for key, value in engine.items()
            if key in database_uri_param
        }

        # Menjalankan query dengan mode SSH
        # SSHTunnelForwarder's func kwargs
        # https://sshtunnel.readthedocs.io/en/latest/#api
        # Setup a SSH Tunnel With the Sshtunnel Module in Python
        # https://blog.ruanbekker.com/blog/2018/04/23/setup-a-ssh-tunnel-with-the-sshtunnel-module-in-python/
        # SSHTunnelForwarder.daemon_forward_servers is not respected:
        # https://github.com/pahaz/sshtunnel/issues/102
        # tunnel without clause:
        # tunnel.daemon_forward_servers = True
        # tunnel.daemon_transport = True
        # tunnel.start()
        # tunnel.stop()
        if ssh_param:
            while True:
                with SSHTunnelForwarder(**ssh_param) as tunnel:
                    try:
                        engine.update({
                            'db_host': tunnel.local_bind_host,
                            'db_port': tunnel.local_bind_port
                        })
                        # Python SSHTunnel w/ Paramiko - CLI works, but not in
                        # script
                        # https://stackoverflow.com/questions/39945269/python-sshtunnel-w-paramiko-cli-works-but-not-in-script
                        sleep(1)
                        result = query(
                            engine,
                            string,
                            **kwargs
                        )
                        break
                    except OperationalError:
                        continue
                    except (KeyboardInterrupt, SystemExit):
                        break
                    except Exception:
                        raise

            return result

    # Issue with a python function returning a generator or a normal object
    # https://stackoverflow.com/questions/25313283/issue-with-a-python-function-returning-a-generator-or-a-normal-object
    generator_mode = kwargs.pop('generator_mode', None)

    def __query(engine, string, **kwargs):
        '''
        engine:
        - obj: SQLAlchemy's engine instance.
        - str: Build SQLAlchemy's engine from string database uri.
        - dict: Build SQLAlchemy's engine from database_uri's func kwargs.

        string: str
        - Use for put raw query sql.

        kwargs: dict
        - Optional kwargs can be use for best query result.
            1. json_mode: bool
                - Use json_mode=True if we want result as string dumps json.
            2. debug_mode: bool
                - Use debug_mode=False if you don't want to see error
                information.
            3. fetch_size: int
                - Use for set how many rows use on every fetch.
                - Default value is 100,000.
            4. stream_results: bool
                - Use stream_results=False for update/insert/delete query.
            5. use_charset_utf8: bool
                - Use use_charset_utf8=True for mysql driver if needed.
        '''

        if isinstance(engine, dict):
            url = database_uri(**engine)
        elif isinstance(engine, Engine):
            url = str(engine.url)

        # "set character set" in sqlalchemy?
        # https://groups.google.com/forum/#!topic/sqlalchemy/3kiPusCy8FM
        if (
            url.startswith('mysql')
            and 'charset=utf8' not in url
            and kwargs.get('use_charset_utf8')
        ):
            # Add params to given URL in Python
            # https://stackoverflow.com/questions/2506379/add-params-to-given-url-in-python
            url = list(
                urlparse(url)
            )
            query = dict(
                parse_qsl(url[4])
            )
            query.update({
                'charset': 'utf8'
            })
            url[4] = urlencode(query)
            url = urlunparse(url)

        args = []

        for key in (
            _kwargs := dict(
                filter(
                    lambda kwarg: kwarg[0] not in [
                        'json_mode',
                        'debug_mode',
                        'fetch_size',
                        'stream_results',
                        'use_charset_utf8'
                    ],
                    kwargs.items()
                )
            )
        ):
            param_kwargs = {
                'key': key,
                'type_': String
            }

            for parameter_type, database_column_type in (
                mapping_type := [
                    [float, Float],
                    [int, Integer],
                    [bool, Boolean],
                    [date, Date],
                    [datetime, DateTime],
                    [dict, JSON],
                    [Iterable, ARRAY],
                    [type(None), None]
                ]
            ):
                if (
                    isinstance(
                        (
                            value := _kwargs[key]
                        ),
                        parameter_type
                    )
                    and not isinstance(value, str)
                ):
                    if database_column_type is ARRAY:
                        if url.startswith('postgresql'):
                            child_type = String

                            if (
                                len_value := len(
                                    value := list(value)
                                )
                            ) > 0:
                                temp_type = set()

                                # Try to sample chacking type of array's child.
                                for i in range(10):
                                    for param_type, db_col_type in (
                                        mapping_type[:-1]
                                    ):
                                        if (
                                            isinstance(
                                                (
                                                    child_value := value[
                                                        randint(
                                                            0,
                                                            len_value - 1
                                                        )
                                                    ]
                                                ),
                                                param_type
                                            )
                                            and not isinstance(
                                                child_value,
                                                str
                                            )
                                        ):
                                            temp_type.add(db_col_type)
                                            break

                                if (
                                    len_temp_type := len(temp_type)
                                ) == 1:
                                    child_type = temp_type.pop()
                                elif (
                                    len_temp_type > 2
                                    or (
                                        len_temp_type == 2
                                        and temp_type != {Date, DateTime}
                                    )
                                ):
                                    child_type = JSON

                            # PostgreSQL multidimensional arrays in SQLAlchemy,
                            # not sure of syntax
                            # https://stackoverflow.com/questions/13888537/postgresql-multidimensional-arrays-in-sqlalchemy-not-sure-of-syntax
                            database_column_type = ARRAY(
                                child_type
                                if child_type is not ARRAY
                                else JSON,
                                dimensions=1
                            )
                        else:
                            database_column_type = JSON

                    param_kwargs['type_'] = database_column_type
                    break

            args.append(
                bindparam(**param_kwargs)
            )

        if (
            stream_results := kwargs.get('stream_results')
        ) is None:
            for action_query in ['insert', 'update', 'delete']:
                if action_query in string.lower():
                    stream_results = False
                    break
            else:
                stream_results = True

        # scoped_session(sessionmaker()) or plain sessionmaker() in sqlalchemy?
        # https://stackoverflow.com/questions/6519546/scoped-sessionsessionmaker-or-plain-sessionmaker-in-sqlalchemy
        # NullPool or QueuePool for remote Postgres SQLalchemy connections?
        # https://stackoverflow.com/questions/48364837/nullpool-or-queuepool-for-remote-postgres-sqlalchemy-connections
        session = scoped_session(
            sessionmaker(
                bind=(
                    engine := create_engine(
                        url,
                        poolclass=NullPool,
                        json_serializer=json_serializer
                    )
                ).execution_options(stream_results=stream_results)
            )
        )()

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
                batch = query_result.fetchmany(
                    kwargs.get('fetch_size', 100_000)
                ) if query_result.returns_rows else None

                def to_result(row, json_mode=False):
                    data = dict(
                        column for column in row.items()
                    )
                    return (
                        json_serializer(data)
                        if json_mode else deserialize(data)
                    )

                if not batch:
                    if not query_result.returns_rows:
                        yield to_result(
                            {
                                'affected_row': query_result.rowcount,
                                'query': (
                                    query_result.context.unicode_statement
                                ),
                                'parameters': (
                                    query_result.context.parameters[0]
                                ),
                                'finish_time': datetime.now()
                            },
                            json_mode
                        )

                    break

                rows = batch.__iter__()

                try:
                    prev_row = next(rows)

                    for row in rows:
                        result = to_result(prev_row, json_mode)
                        prev_row = row
                        yield result + ', ' if json_mode else result

                    yield to_result(prev_row, json_mode)
                except StopIteration:
                    pass
                # KeyboardInterrupt and SystemExit should not be wrapped by
                # sqlalchemy #689
                # https://github.com/sqlalchemy/sqlalchemy/issues/689
                # Avoiding accidentally catching KeyboardInterrupt and
                # SystemExit in Python 2.4
                # https://stackoverflow.com/questions/2669750/avoiding-accidentally-catching-keyboardinterrupt-and-systemexit-in-python-2-4
                # Except block handles 'BaseException'
                # https://lgtm.com/rules/6780080/
                # Catch multiple exceptions in one line (except block)
                # https://stackoverflow.com/questions/6470428/catch-multiple-exceptions-in-one-line-except-block
                # How to get the process ID to kill a nohup process?
                # https://stackoverflow.com/questions/17385794/how-to-get-the-process-id-to-kill-a-nohup-process
                # Fixing “Lock wait timeout exceeded; try restarting
                # transaction” for a 'stuck" Mysql table?
                # https://stackoverflow.com/questions/2766785/fixing-lock-wait-timeout-exceeded-try-restarting-transaction-for-a-stuck-my/10315184
                except (KeyboardInterrupt, SystemExit, Exception):
                    break

            if json_mode:
                yield ']'

            query_result.close()
            session.commit()
        except (KeyboardInterrupt, SystemExit, Exception):
            session.rollback()

            if kwargs.get('debug_mode') in [None, True]:
                raise
        finally:
            session.close()
            engine.dispose()

    result = __query(engine, string, **kwargs)

    if not generator_mode:
        result = (
            ''.join(result)
            if kwargs.get('json_mode') is True
            else list(result)
        )

    return result
