#!/usr/bin/env python3

# Copyright 2023 Pipin Fitriadi <pipinfitriadi@gmail.com>

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

# How To By-Pass Cloudflare While Scraping?
# https://blog.octachart.com/how-to-by-pass-cloudflare-while-scraping

from typing import List

from bs4 import BeautifulSoup
import cloudscraper


class Trakteer:
    "Python's Library for https://trakteer.id/"

    URL: str = 'https://trakteer.id'

    def __init__(
        self,
        email: str,
        password: str,
        delay: int = 10,
        browser: str = 'chrome'
    ):
        self.__email = email
        self.__password = password
        self.__scraper = cloudscraper.create_scraper(
            delay=delay, browser=browser
        )

    def __check_auth(self):
        if found_tag := BeautifulSoup(
            self.__scraper.get(self.URL).text, 'html.parser'
        ).find('input', {'name': '_token'}):
            self.__scraper.post(
                f'{self.URL}/login',
                {
                    '_token': found_tag.get('value'),
                    'email': self.__email,
                    'password': self.__password
                }
            )

    def rewards(self, status: str = None, category: str = None) -> List[dict]:
        '''
        :param status: publish, draft, scheduled, archived
        :param category: all, *your-category*
        '''

        self.__check_auth()
        return self.__scraper.get(
            f'{self.URL}/manage/showcase/fetch',
            params={'status': status, 'category': category}
        ).json()['data']
