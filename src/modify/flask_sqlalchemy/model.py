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

from flask_sqlalchemy.model import Model as _Model
from sqlalchemy import inspect
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList


class Model(_Model):
    db = None

    def to_dict(self):
        # Convert sqlalchemy row object to python dict
        # https://stackoverflow.com/questions/1958219/convert-sqlalchemy-row-object-to-python-dict
        return {
            parameter.key: getattr(self, parameter.key)
            for parameter in inspect(self).mapper.column_attrs
        }

    def __iter__(self):
        # Python dictionary from an object's fields
        # https://stackoverflow.com/questions/61517/python-dictionary-from-an-objects-fields
        for key, value in self.to_dict().items():
            yield key, value

    @classmethod
    def create_session(cls, options=None):
        # Commit changes for only one SQLAlchemy model instance when multiple
        # have changed
        # https://stackoverflow.com/questions/37191141/commit-changes-for-only-one-sqlalchemy-model-instance-when-multiple-have-changed
        # Python sqlalchemy.orm.sessionmaker() Examples
        # https://www.programcreek.com/python/example/51135/sqlalchemy.orm.sessionmaker
        return cls.db.create_session(
            options if isinstance(options, dict)
            else {}
        )()

    @classmethod
    def commit(cls, session, only_read=False):
        try:
            if not only_read:
                session.commit()
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
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def create(cls, row):
        if not isinstance(row, cls):
            raise TypeError(
                f'It should be { cls.__name__ } instance!'
            )

        (
            session := cls.create_session()
        ).add(row)
        cls.commit(session)

    @classmethod
    def read(cls, criterion=None):
        session = cls.create_session()

        if (
            isinstance(criterion, BinaryExpression)
            or isinstance(criterion, BooleanClauseList)
            or isinstance(criterion, bool)
        ):
            data = session.query(cls).filter(criterion).all()
        elif criterion is None:
            data = session.query(cls).all()
        else:
            data = session.query(cls).get(criterion)

        cls.commit(session, True)
        return data

    @classmethod
    def update(
        cls,
        criterion,
        values,
        synchronize_session='evaluate',
        update_args=None
    ):
        data = (
            session := cls.create_session()
        ).query(cls).filter(criterion).update(
            values,
            synchronize_session,
            update_args
        )
        cls.commit(session)
        return data

    @classmethod
    def delete(cls, ident=None):
        session = cls.create_session()
        result = None

        if ident and (
            data := cls.read(ident)
        ):
            session.delete(data)
        elif ident is None:
            result = session.query(cls).delete()

        cls.commit(session)
        return result
