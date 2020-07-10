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

from flask import current_app
from flask_sqlalchemy import BaseQuery, SQLAlchemy as _SQLAlchemy

from .model import Model
from ... import Query as VoxrowQuery

try:
    from ....config import DB_SCHEMA
except Exception:
    DB_SCHEMA = 'VOXROW'


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

        # Variable ini dipergunakan di voxrow.modify.flask_sqlalchemy.model
        self.Model.db = self

    def query(self, string, **kwargs):
        if kwargs.get('debug_mode') is None:
            kwargs['debug_mode'] = current_app.debug

        bind_key = kwargs.pop('bind_key', None)
        return VoxrowQuery(
            self.get_engine(
                *(
                    (current_app, bind_key)
                    if isinstance(bind_key, str)
                    else (current_app,)
                )
            )
        )(string, **kwargs)


SQLAlchemy.query.__doc__ = (
    VoxrowQuery.__call__.__doc__
    + '''    6. bind_key: str
                - Use it if we have more than one database in one system.
    '''
)
