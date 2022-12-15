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

from flask import Blueprint
from sqlalchemy.schema import CreateSchema, DropSchema

from ... import blueprint_name
from ...extension.model import db, User
from ...modify.flask_sqlalchemy import DB_SCHEMA

app = Blueprint(
    (
        app_name := blueprint_name(__file__)
    ),
    __name__,
    cli_group=app_name
)


def database_setup():
    with db.engine.connect() as conn:
        # SQLAlchemy: “create schema if not exists”
        # https://stackoverflow.com/questions/50927740/sqlalchemy-create-schema-if-not-exists
        if not conn.dialect.has_schema(conn, DB_SCHEMA):
            # Getting SQLAlchemy to issue CREATE DB SCHEMA on create_all
            # https://stackoverflow.com/questions/13677781/getting-sqlalchemy-to-issue-create-schema-on-create-all
            db.engine.execute(
                CreateSchema(DB_SCHEMA)
            )

    db.create_all()

    if not User.read():
        User.create(
            User(
                username='admin',
                password='admin1234',
                is_admin=True
            )
        )


@app.before_app_first_request
def before_app_first_request():
    database_setup()


@app.cli.command('create')
def create_database():
    # Command Line Interface
    # https://flask.palletsprojects.com/en/1.1.x/cli/
    database_setup()


@app.cli.command('drop')
def drop_database():
    db.drop_all()

    with db.engine.connect() as conn:
        if conn.dialect.has_schema(conn, DB_SCHEMA):
            db.engine.execute(
                DropSchema(DB_SCHEMA)
            )
