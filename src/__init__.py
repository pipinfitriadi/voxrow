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

import __main__ as main
from datetime import date, datetime
from itertools import zip_longest
from json import (
    dumps,
    JSONDecoder as _JSONDecoder,
    JSONEncoder as _JSONEncoder,
    loads
)
from json.decoder import JSONDecodeError, WHITESPACE
from pathlib import Path
import re
from statistics import mean
from sys import exc_info
from traceback import print_exception

STRING_DATE_FORMAT = '%Y-%m-%d'
STRING_DATETIME_FORMAT = f'{ STRING_DATE_FORMAT }T%H:%M:%S'


def display_time(seconds, granularity=2, sort_name=False):
    def text_result(value, name, sort_name):
        if sort_name:
            name = name[0]
        elif value in range(2):
            name = name.rstrip('s')

        return f"{ value }{ '' if sort_name else ' ' }{ name }"

    # Python function to convert seconds into minutes, hours, and days
    # https://stackoverflow.com/questions/4048651/python-function-to-convert-seconds-into-minutes-hours-and-days
    def result(seconds):
        check_granularity = 0
        SECOND = 1
        MINUTE = SECOND * 60
        HOUR = MINUTE * 60
        DAY = HOUR * 24
        WEEK = DAY * 7

        for name, count in {
            'weeks': WEEK,
            'days': DAY,
            'hours': HOUR,
            'minutes': MINUTE,
            'seconds': SECOND,
        }.items():
            value = seconds // count

            if value:
                yield text_result(value, name, sort_name)
                check_granularity += 1

                if check_granularity >= granularity:
                    break
                else:
                    seconds -= value * count
        else:
            if not check_granularity:
                yield text_result(value, name, sort_name)

    return (' ' if sort_name else ', ').join(
        list(
            result(seconds)
        )
    )


class Log:
    def __init__(self, file_name=None):
        self.__PROCESS_TIME = []
        self.__START_TIME = datetime.now()
        self.__LAST_TIME = self.__START_TIME
        self.__FILE_NAME = file_name

        if not self.__FILE_NAME and hasattr(main, '__file__'):
            # Get name of current script in Python
            # https://stackoverflow.com/questions/4152963/get-name-of-current-script-in-python
            self.__FILE_NAME = f'{ blueprint_name(main.__file__) }.log'

        if self.__FILE_NAME:
            with open(self.__FILE_NAME, 'w'):
                pass

    def __call__(self, *data, sep=' | ', end='\n'):
        last_time = datetime.now()
        self.__PROCESS_TIME.append(
            (last_time - self.__LAST_TIME).seconds
        )
        self.__LAST_TIME = last_time
        total_time = (self.__LAST_TIME - self.__START_TIME).seconds
        average_time = round(
            mean(self.__PROCESS_TIME)
        )

        for d in data:
            if isinstance(d, Exception):
                is_error = True
                error = d
                break
        else:
            is_error = False

        if not is_error:
            data = [
                self.__LAST_TIME.strftime(STRING_DATETIME_FORMAT),
                f'TOTAL: { display_time(total_time, 3, True) }',
                f'AVG: { display_time(average_time, 3, True) }',
                *data
            ]
            print(
                *data,
                sep=sep,
                end=end
            )

        if self.__FILE_NAME:
            # Convert bytes to a string
            # https://stackoverflow.com/questions/606191/convert-bytes-to-a-string
            # How to seek and append to a binary file in python
            # https://stackoverflow.com/questions/4388201/how-to-seek-and-append-to-a-binary-file-in-python
            # Remove very last character in file
            # https://stackoverflow.com/questions/18857352/remove-very-last-character-in-file
            # Writing to a File with Python's print() Function
            # https://stackabuse.com/writing-to-a-file-with-pythons-print-function/
            with open(self.__FILE_NAME, 'a') as log_file:
                if is_error:
                    # Python: How to write error in the console in txt file?
                    # https://stackoverflow.com/questions/55169364/python-how-to-write-error-in-the-console-in-txt-file
                    # How to print the full traceback without halting the
                    # program
                    # https://stackoverflow.com/questions/3702675/how-to-print-the-full-traceback-without-halting-the-program
                    print_exception(*exc_info(), file=log_file)
                else:
                    print(*data, sep=sep, end=end, file=log_file)

        if is_error:
            raise error


def blueprint_name(file):
    # How to get the filename without the extension from a path in Python?
    # https://stackoverflow.com/questions/678236/how-to-get-the-filename-without-the-extension-from-a-path-in-python
    path = Path(file)
    name = (path).resolve().stem

    if name == '__init__':
        name = path.parent.resolve().stem

    return name


# How to convert string int JSON into real int with json.loads
# https://stackoverflow.com/questions/45068797/how-to-convert-string-int-json-into-real-int-with-json-loads
# How to convert to a Python datetime object with JSON.loads?
# https://stackoverflow.com/questions/8793448/how-to-convert-to-a-python-datetime-object-with-json-loads
def deserialize(object):
    '''
    >>> deserialize('2020-04-28'), deserialize('2020-04-28T15:00:46')
    '''

    if isinstance(object, str):
        try:
            object = loads(object)
        except JSONDecodeError:
            pass

        if isinstance(object, str):
            for regex, str_time_format in [
                [
                    r'^\d{4}-\d{2}-\d{2}$',
                    STRING_DATE_FORMAT
                ],
                [
                    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',
                    STRING_DATETIME_FORMAT
                ]
            ]:
                if re.match(regex, object):
                    is_time = False

                    try:
                        object = datetime.strptime(object, str_time_format)

                        is_time = True
                    except Exception:
                        pass

                    if is_time:
                        break
        else:
            object = deserialize(object)
    elif isinstance(object, dict):
        object = {
            key: deserialize(value)
            for key, value in object.items()
        }
    elif isinstance(object, list):
        object = [
            deserialize(value)
            for value in object
        ]

    return object


class JSONDecoder(_JSONDecoder):
    def decode(self, s, _w=WHITESPACE.match):
        return deserialize(
            super().decode(s, _w)
        )


class JSONEncoder(_JSONEncoder):
    '''
    >>> from json import dumps
    >>> dumps(object, cls=JSONEncoder)
    '''

    # Custom JSON encoder for Flask
    # https://gist.github.com/claraj/3b2b95a62c5ba6860c03b5c737c214ab
    # Pass user built json encoder into Flask's jsonify
    # https://stackoverflow.com/questions/44146087/pass-user-built-json-encoder-into-flasks-jsonify/44158611
    def default(self, obj):
        return (
            super().default(obj)
            if isinstance(obj, str)
            else serialize(obj)
        )


def serialize(object):
    '''
    >>> from json import dumps
    >>> dumps(object, default=serialize)
    '''

    # How to serialize a datetime object as JSON using Python?
    # https://code-maven.com/serialize-datetime-object-as-json-in-python
    if isinstance(object, datetime):
        object = object.strftime(STRING_DATETIME_FORMAT)
    elif isinstance(object, date):
        object = object.strftime(STRING_DATE_FORMAT)
    elif isinstance(object, set):
        object = list(object)

    return object


def json_serializer(object):
    return dumps(object, cls=JSONEncoder)


def json_deserializer(object):
    return loads(object, cls=JSONDecoder)


def masking_text(
    text: str,
    masking_percentage: float = .65,
    masking_direction_start_from: str = 'right',
    masking_char: str = '*'
) -> str:
    '''
        masking_direction_start_from:
        - right
        - left
        - inner
        - outer
    '''

    text = str(text)
    non_words = [non_word for non_word in re.split(r'\w', text) if non_word]
    words = []

    for word in re.split(r'\W', text):
        if word:
            last_char_non_masking = int(
                len(word) * (1 - masking_percentage) - 1
            )

            if masking_direction_start_from in ['left', 'right']:
                word = ''.join(
                    char if i <= last_char_non_masking else masking_char
                    for i, char in enumerate(
                        word[::(
                            -1 if masking_direction_start_from == 'left'
                            else None
                        )]
                    )
                )[::(-1 if masking_direction_start_from == 'left' else None)]
            else:
                middle_i = len(word) // 2
                word_is_odd = len(word) % 2
                enum_word = list(enumerate(word))
                word = ''.join(
                    char
                    for _, char in sorted(
                        [
                            (
                                i,
                                (
                                    char
                                    if j <= last_char_non_masking
                                    or i is None
                                    else masking_char
                                )
                            )
                            for j, (i, char) in enumerate([
                                elements
                                for companion in list([
                                    *(
                                        [(
                                            (middle_i, word[middle_i]),
                                            (None, '')
                                        )]
                                        if word_is_odd else []
                                    ),
                                    *zip(
                                        enum_word[:middle_i][::-1],
                                        enum_word[middle_i + (
                                            1 if word_is_odd else 0
                                        ):]
                                    )
                                ])[::(
                                    -1
                                    if masking_direction_start_from == 'inner'
                                    else None
                                )]
                                for elements in companion
                            ])
                        ][::(
                            -1
                            if masking_direction_start_from == 'inner'
                            else None
                        )],
                        key=lambda x: float('inf') if x[0] is None else x[0]
                    )
                )

            words.append(word)

    return ''.join(
        ''.join(elements)
        for elements in zip_longest(
            *(
                (words, non_words)
                if len(words) > len(non_words)
                else (non_words, words)
            ),
            fillvalue=''
        )
    )
