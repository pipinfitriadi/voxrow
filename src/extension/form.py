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

from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

from .model import User
from ..modify.flask_wtf import BooleanField, FlaskForm


class UserForm(FlaskForm):
    username = StringField(
        User.username.property.columns[0].name,
        validators=[
            DataRequired(),
            # How to get sqlalchemy length of a string column
            # https://stackoverflow.com/questions/1777814/how-to-get-sqlalchemy-length-of-a-string-column
            Length(
                # Why is there a minimum username length?
                # https://security.stackexchange.com/questions/46875/why-is-there-a-minimum-username-length
                min=5,
                max=User.username.property.columns[0].type.impl.length
            )
        ]
    )
    password = PasswordField(
        User.password.property.columns[0].name,
        validators=[
            DataRequired(),
            Length(
                min=8,
                max=User.password.property.columns[0].type.impl.length
            )
        ]
    )
    is_admin = BooleanField(
        User.is_admin.property.columns[0].name
    )
