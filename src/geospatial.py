#!/usr/bin/env python3

# Copyright 2022 Pipin Fitriadi <pipinfitriadi@gmail.com>

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

import logging
from typing import Iterator

import requests

HEADERS: dict = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}


def arcgis_data(
    url_service: str,
    url_headers_request: dict = HEADERS,
    result_offset: int = 0,
    units: str = 'esriSRUnit_Meter'
) -> Iterator[dict]:
    total_rows = requests.get(
        url_service,
        {
            'where': '1=1',
            'returnCountOnly': True,
            'f': 'json'
        },
        headers=url_headers_request
    ).json()['count']
    curr_total = 0

    while True:
        response = requests.get(
            url_service,
            {
                'where': '1=1',
                'units': units,
                'outFields': '*',
                'resultOffset': result_offset,
                'f': 'geojson'
            },
            headers=url_headers_request
        ).json()

        for feature in response.get('features', []):
            yield feature
            curr_total += 1
            result_offset += 1

        logging.info(
            ' | '.join([
                'ArcGIS Map Service API',
                f'Progress Fetch Rows (%): {100*curr_total/total_rows:3.0f}%',
                f'Final Total Rows: {total_rows:,}',
                f'Current Total Rows: {curr_total:,}'
            ])
        )
        exceeded_transfer_limit = response.get('exceededTransferLimit')

        if (
            exceeded_transfer_limit is False
            or (
                exceeded_transfer_limit is None
                and not response.get('properties', {}).get(
                    'exceededTransferLimit', False
                )
            )
            or curr_total >= total_rows
        ):
            break
