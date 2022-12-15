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

from flask import abort, Blueprint
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_claims,
    get_jwt_identity,
    get_raw_jwt,
    jwt_required,
    jwt_refresh_token_required
)

from ... import blueprint_name
from ...extension.form import UserForm
from ...extension.model import Token, User

app = Blueprint(
    (
        app_name := blueprint_name(__file__)
    ),
    __name__,
    url_prefix=f'/{ app_name }/'
)


@app.route('/')
@jwt_required
def get():
    return get_jwt_claims()


@app.route('/', methods=['POST'])
def post():
    if (
        form := UserForm()
    ).validate_on_submit():
        error_parameter = {}

        if (
            user := User.read(
                User.username == (
                    username := form.username.data
                )
            )
        ):
            user = user[0]

            if not user.is_password(
                (password := form.password).data
            ):
                error_parameter[password.name] = (
                    f'{ password.name.title() } salah!'
                )
        else:
            error_parameter[form.username.name] = (
                f'{ username } tidak terdaftar!'
            )
    else:
        error_parameter = {
            key: value[0] if len(value) == 1 else value
            for key, value in form.errors.items()
        }

    if error_parameter:
        # Which HTTP code is best suited for validation errors: 400 or 422?
        # https://www.quora.com/Which-HTTP-code-is-best-suited-for-validation-errors-400-or-422
        abort(422, {'parameter': error_parameter})

    data = {
        key: func(user.id)
        for key, func in {
            'access_token': create_access_token,
            'refresh_token': create_refresh_token
        }.items()
    }
    Token.create(
        data['refresh_token']
    )
    return data, 201


@app.route('/', methods=['PUT'])
@jwt_refresh_token_required
def put():
    return {
        'access_token': create_access_token(
            get_jwt_identity()
        )
    }, 201


@app.route('/', methods=['DELETE'])
@jwt_refresh_token_required
def delete():
    Token.update(
        Token.jti == get_raw_jwt()['jti'],
        {'is_revoked': True}
    )
    return (
        f'{ User.read(get_jwt_identity()).username } berhasil logged out!',
        202
    )
