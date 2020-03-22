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
from json import dumps
from os import getenv
from pathlib import Path

from sshtunnel import SSHTunnelForwarder

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

    return object


def to_json(object):
    return dumps(object, default=serialize)


def database_uri(
    db_driver='postgresql',
    db_host='localhost',
    db_port=5432,
    db_name='postgres',
    db_user='',
    db_pass='',
    ssh_host=None,
    ssh_port=22,
    ssh_username=None,
    ssh_password=None
):
    if all((
        ssh_host,
        ssh_port,
        ssh_username,
        ssh_password
    )):
        # Setup a SSH Tunnel With the Sshtunnel Module in Python
        # https://blog.ruanbekker.com/blog/2018/04/23/setup-a-ssh-tunnel-with-the-sshtunnel-module-in-python/
        server = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            remote_bind_address=(db_host, db_port)
        )

        # SSHTunnelForwarder.daemon_forward_servers is not respected:
        # https://github.com/pahaz/sshtunnel/issues/102
        server.daemon_forward_servers = True
        server.daemon_transport = True

        server.start()
        db_host = server.local_bind_host
        db_port = server.local_bind_port

    return (
        (
            f'postgresql://{ db_user }:{ db_pass }@'
            f'{ db_host }:{ db_port }/{ db_name }'
        )
        if db_driver == 'postgresql' else None
    )


def database_uri_from_env(
    db_driver_env='DB_DRIVER',
    db_host_env='DB_HOST',
    db_port_env='DB_PORT',
    db_name_env='DB_NAME',
    db_user_env='DB_USER',
    db_pass_env='DB_PASS',
    ssh_host_env='SSH_HOST',
    ssh_port_env='SSH_PORT',
    ssh_username_env='SSH_USERNAME',
    ssh_password_env='SSH_PASSWORD'
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
        getenv(ssh_host_env),
        int(
            getenv(ssh_port_env, '22')
        ),
        getenv(ssh_username_env),
        getenv(ssh_password_env)
    )

