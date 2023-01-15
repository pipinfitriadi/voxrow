#!/usr/bin/env python3

# Copyright 2022 Pipin Fitriadi <pipinfitriadi@gmail.com>

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
from json import dumps
import logging
from os import getenv, getcwd
from os.path import isfile, join as path_join
import re
from time import sleep
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from jinja2 import Environment, FileSystemLoader
from jinja2.meta import find_referenced_templates, find_undeclared_variables
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import bindparam, create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.exc import OperationalError, StatementError
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.query import Query as _Query
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.sql.expression import null
from sqlalchemy.types import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    JSON,
    NullType,
    String
)

from . import deserialize, json_serializer, serialize


def database_uri(
    db_driver='postgresql+psycopg2',
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
        if db_driver else 'sqlite:///voxrow.db'
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
        getenv(db_driver_env, 'postgresql+psycopg2'),
        getenv(db_host_env, 'localhost'),
        int(
            getenv(db_port_env, '5432')
        ),
        getenv(db_name_env, 'postgres'),
        getenv(db_user_env, ''),
        getenv(db_pass_env, ''),
        getenv(use_charset_utf8_env, 'FALSE').upper() in ['TRUE', '1']
    )


# Retry failed sqlalchemy queries
# https://stackoverflow.com/questions/53287215/retry-failed-sqlalchemy-queries/60614707#60614707
class RetryingQuery(_Query):
    __max_retry_count__ = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __iter__(self):
        attempts = 0

        while True:
            attempts += 1

            try:
                return super().__iter__()
            except OperationalError as ex:
                if 'server closed the connection unexpectedly' not in str(ex):
                    raise

                if attempts <= self.__max_retry_count__:
                    sleep_for = 2 ** (attempts - 1)
                    logging.error(
                        ' [!] Database connection error: retrying Strategy => '
                        f'sleeping for {sleep_for}s and will retry '
                        f'(attempt #{attempts} of {self.__max_retry_count__})'
                        f'\nDetailed query impacted: {ex}'
                    )
                    sleep(sleep_for)
                    continue
                else:
                    raise
            except StatementError as ex:
                if (
                    'reconnect until invalid transaction is rolled back'
                    not in str(ex)
                ):
                    raise
                self.session.rollback()


class Query:
    def __init__(self, engine, use_charset_utf8=False, template_dir=None):
        '''
        engine:
        - obj: SQLAlchemy's engine instance.
        - str: Build SQLAlchemy's engine from string database uri.
        - dict: Build SQLAlchemy's engine from database_uri's func kwargs and
        SSHTunnelForwarder's func kwarg.

        use_charset_utf8: bool
        - Use use_charset_utf8=True for mysql driver if needed.

        template_dir: str
        - Use for set specify jinja2 template directory, os.getcwd()
        value is used as default.
        '''

        self.__template_dir = template_dir if template_dir else getcwd()
        self.__env = Environment(
            loader=FileSystemLoader(self.__template_dir)
        )
        self.__ssh_param = {}
        self.__engine = engine
        self.__use_charset_utf8 = use_charset_utf8

        if isinstance(self.__engine, dict):
            self.__db_host = None
            self.__db_port = None
            database_uri_param = {
                'db_driver',
                'db_host',
                'db_port',
                'db_name',
                'db_user',
                'db_pass',
                'use_charset_utf8'
            }
            self.__ssh_param = {
                key: value
                for key, value in self.__engine.items()
                if key not in database_uri_param
            }
            self.__engine = {
                key: value
                for key, value in self.__engine.items()
                if key in database_uri_param
            }

            if self.__use_charset_utf8:
                self.__engine['use_charset_utf8'] = self.__use_charset_utf8
            elif use_charset_utf8 := self.__engine.get('use_charset_utf8'):
                self.__use_charset_utf8 = use_charset_utf8

    def __call__(self, string, **kwargs):
        '''
        string: str
        - Use for put raw query sql or sql file path. It is support jinja2
        templating.

        kwargs: dict
        - Put sql parameter and or jinja2 variable in here.
        - Optional parameter can be use for best query result:
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
        '''

        if self.__ssh_param:
            ssh_param = self.__ssh_param
            self.__ssh_param = {}

            while True:
                with SSHTunnelForwarder(**ssh_param) as tunnel:
                    # Python SSHTunnel w/ Paramiko - CLI works, but
                    # not in script
                    # https://stackoverflow.com/questions/39945269/python-sshtunnel-w-paramiko-cli-works-but-not-in-script
                    # Menjalankan query dengan mode SSH
                    # SSHTunnelForwarder's func kwargs
                    # https://sshtunnel.readthedocs.io/en/latest/#api
                    # Setup a SSH Tunnel With the Sshtunnel Module in Python
                    # https://blog.ruanbekker.com/blog/2018/04/23/setup-a-ssh-tunnel-with-the-sshtunnel-module-in-python/
                    # SSHTunnelForwarder.daemon_forward_servers is not
                    # respected:
                    # https://github.com/pahaz/sshtunnel/issues/102
                    # tunnel without clause:
                    # tunnel.daemon_forward_servers = True
                    # tunnel.daemon_transport = True
                    # tunnel.start()
                    # tunnel.stop()
                    sleep(1)

                    self.__db_host = tunnel.local_bind_host
                    self.__db_port = tunnel.local_bind_port

                    try:
                        result = self.__call__(string, **kwargs)
                        break
                    except OperationalError as e:
                        if (
                            e.args
                            and e.orig
                            and e.orig.args
                            and (
                                # Error MySQL: Lost Connection
                                'mysql' in e.args[0].lower()
                                and e.orig.args[0] == 2013
                            )
                        ):
                            continue
                        else:
                            raise
                    except (KeyboardInterrupt, SystemExit):
                        break
                    except Exception:
                        raise
                    finally:
                        self.__db_host = None
                        self.__db_port = None

            self.__ssh_param = ssh_param
        else:
            # Issue with a python function returning a generator or a normal
            # object
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

    def __compile(self, text_clause):
        '''
        Function to compile and bind parameter sql.

        text_clause: sqlalchemy.sql.elements.TextClause
        '''

        # SQLAlchemy: print the actual query
        # https://stackoverflow.com/questions/5631078/sqlalchemy-print-the-actual-query
        class StringLiteral(String):
            '''
            Teach SA how to literalize various things.
            '''

            def literal_processor(self, dialect):
                super_processor = super(
                    StringLiteral, self
                ).literal_processor(dialect)

                def process(value):
                    if (
                        isinstance(
                            value := serialize(value),
                            Iterable
                        )
                        and not isinstance(value, str)
                    ):
                        value = dumps(value)

                    if isinstance(
                        result := super_processor(value),
                        bytes
                    ):
                        result = result.decode(dialect.encoding)

                    return result

                return process

        class LiteralDialect(DefaultDialect):
            colspecs = {
                DateTime: StringLiteral,
                Date: StringLiteral,
                JSON: StringLiteral
            }

        return str(
            text_clause.compile(
                dialect=LiteralDialect(),
                compile_kwargs={'literal_binds': True}
            )
        )

    def render(self, string, literal_binds=True, **kwargs):
        '''
        Function for render jinja2 template and bind parameter sql.

        string: str
        - Use for put raw query sql or sql file path. It is support jinja2
        templating.

        literal_binds: bool
        - Use literal_binds=False if not want to see sql bind parameter.

        kwargs: dict
        - Put sql parameter and or jinja2 variable in here.
        - It is mandatory if string have sql parameter and literal_binds=True.
        '''

        # SQLAlchemy: print the actual query
        # https://stackoverflow.com/questions/5631078/sqlalchemy-print-the-actual-query

        def __template_source(template_file):
            '''
            Function for returning jinja2 template source.

            template_file: str
            - Template file path.
            '''

            return self.__env.loader.get_source(self.__env, template_file)[0]

        def jinja2_keys(template_source):
            # Jinja2 load templates from separate location than working
            # directory
            # https://stackoverflow.com/questions/37968787/jinja2-load-templates-from-separate-location-than-working-directory
            # Template Designer Documentation
            # https://jinja.palletsprojects.com/en/2.11.x/templates/
            # How to get list of all variables in jinja 2 templates
            # https://stackoverflow.com/questions/8260490/how-to-get-list-of-all-variables-in-jinja-2-templates
            # The Meta API
            # https://jinja.palletsprojects.com/en/2.11.x/api/
            (
                keys := find_undeclared_variables(
                    parsed_content := self.__env.parse(template_source)
                )
            ).update({
                key
                for ref_template in find_referenced_templates(
                    parsed_content
                )
                for key in jinja2_keys(
                    __template_source(ref_template)
                )
            })
            return keys

        kwargs = {
            key: value
            for key, value in kwargs.items()
            if key not in [
                'json_mode',
                'debug_mode',
                'fetch_size',
                'stream_results'
            ]
        }

        if isinstance(string, str):
            if isfile(
                path_join(self.__template_dir, string)
            ):
                template = self.__env.get_template(string)
                template_source = __template_source(string)
            else:
                template = self.__env.from_string(string)
                template_source = string

            string = template.render(**kwargs)

            for key in (
                jinja2_keys(template_source).intersection(
                    kwargs.keys()
                ) - set(
                    re.findall(
                        r':(\w+)',
                        string
                    )
                )
            ):
                kwargs.pop(key, None)

        args = []

        for key in kwargs:
            param_kwargs = {
                'key': key,
                'type_': String
            }

            if (
                value := kwargs[key]
            ) is None:
                # How to insert NULL value in SQLAlchemy?
                # https://stackoverflow.com/questions/32959336/how-to-insert-null-value-in-sqlalchemy
                kwargs[key] = null()

            for parameter_type, database_column_type in [
                [type(None), NullType],
                [float, Float],
                [int, Integer],
                [bool, Boolean],
                [date, Date],
                [datetime, DateTime],
                [dict, JSON],
                [Iterable, JSON]
            ]:
                if (
                    isinstance(value, parameter_type)
                    and not isinstance(value, str)
                ):
                    param_kwargs['type_'] = database_column_type
                    break

            args.append(
                bindparam(**param_kwargs)
            )

        string = text(string).bindparams(*args, **kwargs)

        if literal_binds:
            string = self.__compile(string)
        elif literal_binds is not None:
            string = str(string)

        return string

    def __query(self, string, **kwargs):
        '''
        Func to get sql query result.

        string: str
        - Use for put raw query sql or sql file path. It is support jinja2
        templating.

        kwargs: dict
        - Put sql parameter and or jinja2 variable in here.
        - Optional parameter can be use for best query result:
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
        '''

        string = self.render(string, None, **kwargs)

        if (
            stream_results := kwargs.get('stream_results')
        ) is None:
            for s in re.findall(
                r"'[^']*'",
                _string := '\n'.join([
                    s
                    for s in re.sub(
                        r'--.*', '', str(string)
                    ).split('\n')
                    if s
                ]),
                flags=re.DOTALL
            ):
                _string = re.sub(
                    s.replace('[', r'\[').replace(']', r'\]'),
                    "''",
                    _string,
                    1
                )

            regex_sql_space = r'\s+(.*\s+)?'

            # Chapter 13 SQL Statements
            # https://dev.mysql.com/doc/refman/5.6/en/sql-statements.html
            for regex in [
                'EXPLAIN',
                'INSERT',
                'SET',
                regex_sql_space.join(['DELETE', 'FROM']),
                regex_sql_space.join(['MERGE', 'INTO', 'USING']),
                'CREATE',
                'ALTER',
                'DROP',
                regex_sql_space.join(['RENAME', 'TABLE']),
                regex_sql_space.join(['TRUNCATE', 'TABLE']),
                'SHOW',
                'DESCRIBE',
                'CALL',
                'DO',
                'HANDLER',
                'LOAD',
                'REPLACE',
                'KILL',
                'GRANT'
            ]:
                if re.findall(
                    fr'\s*{ regex }\s+.*',
                    _string,
                    flags=re.DOTALL + re.IGNORECASE
                ):
                    stream_results = False
                    break
            else:
                stream_results = True
        else:
            stream_results = False

        # Process to returning string database uri.
        if isinstance(self.__engine, dict):
            engine = self.__engine

            if all([
                self.__db_host,
                self.__db_port
            ]):
                engine.update({
                    'db_host': self.__db_host,
                    'db_port': self.__db_port
                })

            url = database_uri(**engine)
        elif isinstance(self.__engine, Engine):
            url = str(self.__engine.url)
        else:
            url = self.__engine

        # "set character set" in sqlalchemy?
        # https://groups.google.com/forum/#!topic/sqlalchemy/3kiPusCy8FM
        if (
            url.startswith('mysql')
            and 'charset=utf8' not in url
            and self.__use_charset_utf8
        ):
            # Add params to given URL in Python
            # https://stackoverflow.com/questions/2506379/add-params-to-given-url-in-python
            (
                query := dict(
                    parse_qsl(
                        (
                            url := list(
                                urlparse(url)
                            )
                        )[4]
                    )
                )
            ).update({'charset': 'utf8'})
            url[4] = urlencode(query)
            url = urlunparse(url)

        # scoped_session(sessionmaker()) or plain sessionmaker() in sqlalchemy?
        # https://stackoverflow.com/questions/6519546/scoped-sessionsessionmaker-or-plain-sessionmaker-in-sqlalchemy
        # how to fix “OperationalError: (psycopg2.OperationalError) server
        # closed the connection unexpectedly”
        # https://stackoverflow.com/questions/55457069/how-to-fix-operationalerror-psycopg2-operationalerror-server-closed-the-conn
        session = scoped_session(
            sessionmaker(
                bind=(
                    engine := create_engine(
                        url,
                        json_serializer=json_serializer,
                        pool_size=10,
                        max_overflow=2,
                        pool_recycle=300,
                        pool_pre_ping=True,
                        pool_use_lifo=True
                    )
                ).execution_options(stream_results=stream_results),
                query_cls=RetryingQuery
            )
        )()

        try:
            query_result = session.execute(string)

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
                    data = dict(row)
                    return (
                        json_serializer(data)
                        if json_mode else deserialize(data)
                    )

                if not batch:
                    if not query_result.returns_rows:
                        yield to_result(
                            {
                                'affected_row': query_result.rowcount,
                                'query': self.__compile(string),
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
