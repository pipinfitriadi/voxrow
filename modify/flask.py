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

from types import GeneratorType

from flask import (
    Flask as _Flask,
    jsonify,
    render_template,
    Response,
    request,
    stream_with_context,
    url_for
)
from jinja2.exceptions import TemplateNotFound
from werkzeug.datastructures import Headers
from werkzeug.exceptions import default_exceptions
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.routing import BuildError, RequestRedirect
from werkzeug.wrappers import Response as ResponseBase

try:
    from ...config import WEB_TITLE
except Exception:
    WEB_TITLE = 'VOXROW'


class Flask(_Flask):
    # Customizing the Flask Response Class
    # https://blog.miguelgrinberg.com/post/customizing-the-flask-response-class

    def __init__(self, *args, **kwargs):
        '''
        Dipergunakan untuk mengabaikan custome func make_response.
        exclude_endpoint: str
        '''

        self.exclude_endpoint = kwargs.pop('exclude_endpoint', None)
        super().__init__(*args, **kwargs)

    def make_response(self, rv):
        '''
        Pilihan value yang dapat dipergunakan pada function:
        - rv = response
        - rv = (response, status, headers, template, template_mimetype)
        - rv = (response, status, headers, template)
        - rv = (response, headers, template, template_mimetype)
        - rv = (response, status, template, template_mimetype)
        - rv = (response, template, template_mimetype)
        - rv = (response, headers, template)
        - rv = (response, status, template)
        - rv = (response, template)
        - rv = (response, headers)
        - rv = (response, status)

        Tipe data:
        - template: str = None
        - template_mimetype: str = 'text/html'
        - template_mimetype: bool = True
            Apabila nilainya bool True, maka tidak akan dilakukan pengecekan
            Header Accept Request.
        '''

        status = headers = template = None
        template_mimetype = 'text/html'

        if isinstance(rv, tuple):
            header_type = (Headers, dict, tuple, list)
            len_rv = len(rv)

            if len_rv == 5:
                rv, status, headers, template, template_mimetype = rv
            elif len_rv == 4:
                rv, status, headers, template = rv
            elif len_rv == 3:
                if isinstance(rv[2], str):
                    if isinstance(rv[1], str):
                        rv, template, template_mimetype = rv
                    elif isinstance(rv[1], header_type):
                        rv, headers, template = rv
                    else:
                        rv, status, template = rv
                else:
                    rv, status, headers = rv
            elif len_rv == 2:
                if isinstance(rv[1], str):
                    rv, template = rv
                elif isinstance(rv[1], header_type):
                    rv, headers = rv
                else:
                    rv, status = rv
            else:
                raise TypeError(
                    'The view function did not return a valid'
                    ' response. The return type must be a string, dict, tuple'
                    ' (with max length no more than 5), Response instance, or'
                    ' WSGI callable, but it was a'
                    f' {rv.__class__.__name__}.'
                )

        if (
            not isinstance(rv, self.response_class)
            and not isinstance(rv, ResponseBase)
            and not isinstance(rv, RequestRedirect)
        ):
            if status and status >= 400:
                if isinstance(rv, dict):
                    message = rv.get('error_message')
                    name = rv.get('error_name')
                    parameter = rv.get('error_parameter')
                else:
                    message = default_exceptions[status].description
                    # Flask - How to create custom abort() code?
                    # https://stackoverflow.com/questions/12285903/flask-how-to-create-custom-abort-code/38648607#38648607
                    name = HTTP_STATUS_CODES[status]
                    parameter = {}

                message = str(message) if message else ''

                try:
                    message = (
                        f'{ message } '
                        f'To make { WEB_TITLE } works, please see the'
                        ' Doc in here:'
                        f' { url_for("doc.show", _external=True) }'
                    )
                except BuildError:
                    pass

                data = {
                    'data': None,
                    'error': {
                        'code': status,
                        'message': message,
                        'name': name,
                        'parameter': parameter if parameter else {}
                    }
                }
            elif isinstance(rv, GeneratorType):
                # How to check if an object is a generator object in python
                # https://stackoverflow.com/questions/6416538/how-to-check-if-an-object-is-a-generator-object-in-python
                def generator(rv):
                    yield '{"data": '
                    yield from rv
                    yield ', "error": null}'

                data = generator(rv)
            else:
                data = {
                    'data': rv,
                    'error': None
                }

            if (
                (endpoint := request.endpoint) != self.exclude_endpoint
                or (
                    endpoint == self.exclude_endpoint
                    and (
                        endpoint is None
                        or url_for(endpoint) != request.path
                    )
                )
            ):
                if (
                    isinstance(rv, GeneratorType)
                    and (
                        status is None
                        or (
                            status
                            and status < 400
                        )
                    )
                ):
                    # Python flask.stream_with_context() Examples
                    # https://www.programcreek.com/python/example/58918/flask.stream_with_context
                    rv = Response(
                        stream_with_context(data),
                        mimetype='application/json'
                    )
                elif (
                    template
                    and (
                        template_mimetype is True
                        or request.accept_mimetypes.best == template_mimetype
                    )
                ):
                    try:
                        rv = render_template(
                            template,
                            data=data
                        )
                    except TemplateNotFound:
                        rv = jsonify(data)
                else:
                    rv = jsonify(data)
        elif isinstance(rv, ResponseBase):
            try:
                if (
                    '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
                    "<title>Redirecting...</title>\n"
                    "<h1>Redirecting...</h1>\n"
                    "<p>You should be redirected automatically to target URL: "
                    '<a href="'
                ) in rv.data.decode('utf-8'):
                    rv.data = render_template('redirecting.html').encode()
            except RuntimeError:
                pass
            except TemplateNotFound:
                pass

        return super().make_response(
            (rv, status, headers)
        )
