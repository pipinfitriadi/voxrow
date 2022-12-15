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
from werkzeug.exceptions import default_exceptions, HTTPException

from ... import blueprint_name

app = Blueprint(
    (
        app_name := blueprint_name(__file__)
    ),
    __name__
)


@app.app_errorhandler(HTTPException)
def default_error(error):
    '''
    >>> from flask import abort
    >>> # Cara penggunaan abort ke-1
    >>> abort(400)
    >>> # Cara penggunaan abort ke-2
    >>> abort(400, 'Ini error.')
    >>> # Cara penggunaan abort ke-3
    >>> abort(
    ...  400,
    ...  {
    ...   'paremeter': {'name': 'name harus diisi'},
    ...   'description': 'Ini error.'
    ...  }
    ... )
    '''

    # Google JSON guide:
    # https://stackoverflow.com/questions/12806386/standard-json-api-response-format
    # HTTP status code for “could not fulfill request for *known* reason”:
    # https://stackoverflow.com/questions/33815690/http-status-code-for-could-not-fulfill-request-for-known-reason
    # Flask - How to create custom abort() code?
    # https://stackoverflow.com/questions/12285903/flask-how-to-create-custom-abort-code
    if isinstance(data := error.description, dict):
        parameter = data.get('parameter', {})
        message = data.get('description', None)

        if not message:
            message = default_exceptions[error.code].description
    else:
        parameter = {}
        message = error.description

    return {
        'error_message': message,
        'error_name': error.name,
        'error_parameter': parameter
    }, error.code, '__error__.html.j2'
