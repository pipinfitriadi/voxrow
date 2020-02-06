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
from sqlalchemy.exc import IntegrityError

from ... import blueprint_name
from ...extension.form import UserForm
from ...extension.model import User
from ...extension.token import admin_required

app = Blueprint(
    (
        app_name := blueprint_name(__file__)
    ),
    __name__,
    url_prefix=f'/{ app_name }/'
)


def to_dict(user):
    return {
        key: value
        for key, value in user
        if key != 'password'
    }


@app.route('/')
@app.route(route_id := '/<int(min=1):id>/')
@admin_required
def get(id=None):
    if id and (
        data := User.read(id)
    ):
        data = to_dict(data)
    elif not id:
        data = list(
            to_dict(user)
            for user in User.read()
        )
    else:
        abort(404)

    return data


@app.route('/', methods=['POST'])
@admin_required
def post():
    if (
        form := UserForm()
    ).validate_on_submit():
        error_parameter = {}
        is_admin = form.is_admin.data

        try:
            User.create(
                User(
                    username=(
                        username := form.username.data
                    ),
                    password=form.password.data,
                    is_admin=(
                        is_admin if is_admin else False
                    )
                )
            )
        except IntegrityError:
            error_parameter[form.username.name] = (
                f'{ username } sudah terdaftar!'
            )
    else:
        error_parameter = {
            key: value[0] if len(value) == 1 else value
            for key, value in form.errors.items()
        }

    if error_parameter:
        abort(422, {'parameter': error_parameter})

    return to_dict(
        User.read(User.username == username)[0]
    ), 201


@app.route(route_id, methods=['PUT'])
@admin_required
def put(id):
    if not User.read(id):
        abort(404)

    (
        form := UserForm()
    ).validate_on_submit()
    error_parameter = {}
    parameter = {}

    for key, value in form.data.items():
        if (
            value or (
                key == 'is_admin'
                and value is False
            )
        ):
            if (
                error := form.errors.get(key)
            ):
                error_parameter[key] = (
                    error[0]
                    if len(error) == 1
                    else error
                )
            else:
                parameter[key] = value

    try:
        if not error_parameter and parameter:
            User.update(User.id == id, parameter)
    except IntegrityError:
        error_parameter[form.username.name] = (
            f'{ form.username.data } sudah terdaftar!'
        )

    if error_parameter:
        abort(422, {'parameter': error_parameter})

    return to_dict(
        User.read(id)
    ), 201


@app.route(route_id, methods=['DELETE'])
@admin_required
def delete(id):
    if (
        data := User.read(id)
    ):
        User.delete(id)
    else:
        abort(404)

    return to_dict(data), 202
