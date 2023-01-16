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
# VeNoMouS/cloudscraper: A Python module to bypass Cloudflare's anti-bot page.
# https://github.com/VeNoMouS/cloudscraper
# How to share cookies between Selenium and requests in Python
# https://medium.com/geekculture/how-to-share-cookies-between-selenium-and-requests-in-python-d36c3c8768b

import logging
from time import sleep
from typing import List

from bs4 import BeautifulSoup
import cloudscraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


class Scrape:
    def __init__(self, delay: int = 10, browser: str = 'chrome', **kwargs):
        self._scraper = cloudscraper.create_scraper(
            delay=delay, browser=browser, **kwargs
        )

    def _parser(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, 'html.parser')


class Trakteer(Scrape):
    "Python's Library for https://trakteer.id/"

    URL: str = 'https://trakteer.id'

    def __init__(
        self,
        email: str,
        password: str,
        delay: int = 10,
        browser: str = 'chrome',
        headless: bool = False,
        **kwargs
    ):
        self.__email = email
        self.__password = password
        self.__headless = headless
        self._driver = None
        super().__init__(delay, browser, **kwargs)

    def __enter__(self):
        options = Options()

        if self.__headless:
            options.add_argument('--headless')

        self._driver = webdriver.Chrome(
            service=ChromeService(
                ChromeDriverManager().install()
            ),
            options=options
        )
        return self

    def use_driver(func):
        def wrapper(self, *args, **kwargs):
            if self._driver:
                self._check_auth(True)
                func(self, *args, **kwargs)
            else:
                logging.error('Works only in The Python with statement!')

        return wrapper

    def __wait_until_page_loaded(self):
        while True:
            sleep(7)
            if 'complete' == self._driver.execute_script(
                'return document.readyState;'
            ):
                logging.info(f'{self._driver.current_url} page has loaded')
                break

            logging.info(f'{self._driver.current_url} page still loading')

    def __logout(self):
        self._scraper.get(f'{self.URL}/logout')

    def __exit__(self, exception_type, exception_value, traceback):
        self.__logout()
        self._driver.quit()
        logging.info(f'Successfully logged out from {self.URL}')

    def __token(self, url: str) -> str:
        if token := self._parser(
            self._scraper.get(url).text
        ).find('input', {'name': '_token'}):
            token = token['value']

        return token

    def _check_auth(self, use_driver: bool = False):
        if token := self.__token(self.URL):
            self._scraper.post(
                f'{self.URL}/login',
                {
                    '_token': token,
                    'email': self.__email,
                    'password': self.__password
                }
            )
            logging.info(f'Successfully logged in to {self.URL}')

        if use_driver and not self._driver.get_cookies():
            self._driver.get(self.URL)

            for key, value in self._scraper.cookies.get_dict().items():
                self._driver.add_cookie({'name': key, 'value': value})

            self._driver.get(self.URL)

    def rewards(self, status: str = None, category: str = None) -> List[dict]:
        '''
        :param status: publish, draft, scheduled, archived
        :param category: all, *your-category*
        '''

        self._check_auth()
        return self._scraper.get(
            f'{self.URL}/manage/showcase/fetch',
            params={'status': status, 'category': category}
        ).json()['data']

    @use_driver
    def reward_update(self, id: str, unit_price: int):
        self._driver.get(f'{self.URL}/manage/showcase/{id}/edit')
        self.__wait_until_page_loaded()
        self._driver.execute_script(
            "arguments[0].setAttribute('value', arguments[1]);",
            self._driver.find_element(by=By.NAME, value='required_item'),
            unit_price
        )
        self._driver.execute_script(
            'arguments[0].click();',
            self._driver.find_element(by=By.ID, value='form-submit-button')
        )
        self.__wait_until_page_loaded()
