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

from datetime import datetime

from flask_jwt_extended import decode_token
from sqlalchemy import (
    Column,
    ForeignKey
)
from sqlalchemy.orm import validates
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.types import (
    Boolean,
    DateTime,
    Integer,
    String
)

from ..modify.flask_sqlalchemy import DB_SCHEMA
from ..modify.flask_sqlalchemy import SQLAlchemy
from ..modify.flask_sqlalchemy.types import Password, Username

db = SQLAlchemy()
relationship = db.relationship
Model = db.Model


class User(Model):
    # Define minimum length for PostgreSQL string column with SQLAlchemy
    # https://stackoverflow.com/questions/50174325/define-minimum-length-for-postgresql-string-column-with-sqlalchemy
    __table_args__ = (
        CheckConstraint(
            'char_length(username) >= 5',
            name='username_min_length'
        ),
        CheckConstraint(
            'char_length(password) >= 8',
            name='password_min_length'
        ),
        # Table Configuration
        # https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/table_config.html
        {'schema': DB_SCHEMA}
    )

    id = Column(Integer, primary_key=True)
    is_admin = Column(
        Boolean,
        default=False,
        nullable=False
    )
    username = Column(
        # What is the maximum length of a facebook name?
        # https://stackoverflow.com/questions/8078939/what-is-the-maximum-length-of-a-facebook-name
        Username(50),
        unique=True,
        nullable=False
    )
    # What's the maximum number of characters permitted for the password of a
    # Google Account?
    # https://webapps.stackexchange.com/questions/57947/whats-the-maximum-number-of-characters-permitted-for-the-password-of-a-google-a
    password = Column(Password(100), nullable=False)
    # One-to-Many Relationships¶
    # https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/
    token = relationship(
        'Token',
        backref='user',
        # {DetachedInstanceError} Parent instance <Car> is not bound to a
        # session; lazy load operation of attribute 'owner' cannot proceed
        # https://stackoverflow.com/questions/27701573/detachedinstanceerror-parent-instance-car-is-not-bound-to-a-session-lazy-lo
        lazy='subquery'
    )

    @validates('username')
    def validate_username(self, key, username) -> str:
        if len(username) < 5:
            raise ValueError('username too short')

        return username

    @validates('password')
    def validate_password(self, key, password) -> str:
        if len(password) < 8:
            raise ValueError('password too short')

        return password

    def is_password(self, password):
        return Password.is_correct(self.password, password)

    @classmethod
    def delete(cls, ident=None):
        users = cls.read(ident)

        def delete_token(user):
            for token in user.token:
                Token.delete(token.id)

        if ident and users:
            delete_token(users)
        else:
            for user in users:
                delete_token(user)

        return super().delete(ident)


class Token(Model):
    __table_args__ = {'schema': DB_SCHEMA}

    # Blacklist with a database
    # https://github.com/vimalloc/flask-jwt-extended/tree/master/examples/database_blacklist
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        # specifying schema name in model gives error
        # https://github.com/pallets/flask-sqlalchemy/issues/172
        ForeignKey(f'{ DB_SCHEMA }.user.id'),
        nullable=False
    )
    jti = Column(String(36), nullable=False)
    token_type = Column(String(10), nullable=False)
    expires = Column(DateTime, nullable=True)
    is_revoked = Column(
        Boolean,
        default=False,
        nullable=False
    )

    @classmethod
    def create(cls, token_or_row):
        if isinstance(token_or_row, str):
            token_or_row = cls(
                user_id=(
                    token := decode_token(token_or_row)
                )['identity'],
                jti=token['jti'],
                token_type=token['type'],
                expires=datetime.fromtimestamp(
                    token.get('exp')
                ) if token.get('exp') else None
            )

        cls.update(
            # flake8 complains on boolean comparison “==” in filter clause
            # https://stackoverflow.com/questions/18998010/flake8-complains-on-boolean-comparison-in-filter-clause
            (cls.is_revoked == False) # noqa
            & (
                (cls.user_id == token_or_row.user_id)
                | (cls.expires <= datetime.now())
            ),
            {'is_revoked': True}
        )
        super().create(token_or_row)
