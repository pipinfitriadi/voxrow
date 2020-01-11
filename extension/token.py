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

from functools import wraps

from flask import abort
from flask_jwt_extended import (
    get_jwt_identity,
    JWTManager,
    verify_jwt_in_request
)

from .model import Token, User

jwt = JWTManager()


def admin_required(fn):
    # Custom Decorators
    # https://flask-jwt-extended.readthedocs.io/en/stable/custom_decorators/
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()

        if (
            user := User.read(
                get_jwt_identity()
            )
        ):
            result = fn(*args, **kwargs)

            if not user.is_admin:
                abort(403)
        else:
            result = revoked_token_loader()

        return result

    return wrapper


@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    # Storing Data in Access Tokens
    # https://flask-jwt-extended.readthedocs.io/en/stable/add_custom_data_claims/
    (
        data := dict(
            User.read(identity)
        )
    ).pop('password', None)
    return data


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    # Blacklist and Token Revoking
    # https://flask-jwt-extended.readthedocs.io/en/stable/blacklist_and_token_revoking/
    return (
        # Memastikan token terdaftar
        len(
            Token.read(
                Token.jti == (
                    jti := decrypted_token['jti']
                )
            )
        ) == 0
        # Memastikan token tidak masuk daftar blacklist
        or len(
            Token.read(
                (Token.is_revoked == True) # noqa
                & (Token.jti == jti)
            )
        ) > 0
    )


# Changing Default Behaviors
# https://flask-jwt-extended.readthedocs.io/en/stable/changing_default_behavior/


def default_error(code=401, message=None):
    if code == 401:
        name = 'Unauthorized'
    elif code == 422:
        name = 'Unprocessable Entity'
    else:
        code = 500
        name = 'Internal Server Error'

    return {
        'error_message': message,
        'error_name': name
    }, code


@jwt.expired_token_loader
def expired_token_loader():
    return default_error(401, 'Token has expired.')


@jwt.invalid_token_loader
def invalid_token_loader(callback):
    return default_error(422, f'{ callback }.')


@jwt.revoked_token_loader
def revoked_token_loader():
    return default_error(401, 'Token has been revoked.')


@jwt.unauthorized_loader
def unauthorized_loader(callback):
    return default_error(401, f'{ callback }.')
