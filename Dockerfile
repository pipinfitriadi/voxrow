# MIT License

# Copyright (c) 2019 Pipin Fitriadi <pipinfitriadi@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

FROM python:3.8-alpine
LABEL maintainer="pipinfitriadi@gmail.com"

COPY requirements.txt /tmp/

RUN apk add \
        --no-cache \
        --virtual .build-deps \
        # Cannot “pip install cryptography” in Docker Alpine Linux 3.3 with OpenSSL 1.0.2g and Python 2.7
        # https://stackoverflow.com/questions/35736598/cannot-pip-install-cryptography-in-docker-alpine-linux-3-3-with-openssl-1-0-2g
        gcc \
        musl-dev \
        libffi-dev \
        build-base \
        # How to fix: fatal error: openssl/opensslv.h: No such file or directory in RedHat 7
        # https://stackoverflow.com/questions/46008624/how-to-fix-fatal-error-openssl-opensslv-h-no-such-file-or-directory-in-redhat
        openssl-dev \
    # git not found in alpine image
    # https://github.com/nodejs/docker-node/issues/586
    && apk add --no-cache git \
    && pip install \
        --no-cache-dir \
        --upgrade pip \
    && pip install \
        --no-cache-dir \
        -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + \
    && runDeps="$( \
        scanelf --needed --nobanner --recursive /usr/local \
            | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
            | sort -u \
            | xargs -r apk info --installed \
            | sort -u \
        )" \
    && apk add --virtual .rundeps $runDeps \
    && apk del --no-cache .build-deps
