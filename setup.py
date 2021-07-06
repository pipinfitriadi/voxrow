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

# Packing and deploying a project to Pip
# https://medium.com/@ssbothwell/packing-and-deploying-a-project-to-pip-bcd628d02f6f
# Including files in source distributions with MANIFEST.in
# https://packaging.python.org/guides/using-manifest-in/

from setuptools import setup

setup(
    name='voxrow',
    packages=[
        'voxrow',
        'voxrow.modify',
        'voxrow.extension.route',
        'voxrow.extension',
        'voxrow.modify.flask_sqlalchemy'
    ],
    package_dir={
        'voxrow': '',
        'voxrow.extension': 'extension',
        'voxrow.extension.route': 'extension/route',
        'voxrow.modify': 'modify',
        'voxrow.modify.flask_sqlalchemy': 'modify/flask_sqlalchemy'
    },
    package_data={
        'voxrow': [
            'server/Makefile',
            'server/docker-compose/letsencrypt.yml',
            'server/install/*',
            'server/nginx/*'
        ]
    },
    version='0.9.15',
    description=(description := "VOXROW's library"),
    long_description=description,
    author='Pipin Fitriadi',
    author_email='pipinfitriadi@gmail.com',
    license='MS-RSL',
    url='https://gitlab.com/voxrow/voxrow',
    install_requires=[
        'flake8',
        'flask',
        'flask-jwt-extended',
        'Flask-SQLAlchemy',
        'Flask-WTF',
        'cryptography==3.2.1',
        'sshtunnel'
    ],
    download_url=(
        'https://gitlab.com/voxrow/voxrow/-/archive/master/'
        'voxrow-master.tar.gz'
    ),
    keywords=['voxrow', 'library', 'raw sql query'],
    python_requires='>=3.8.0',
    platforms='any'
)
