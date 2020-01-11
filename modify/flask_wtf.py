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

from flask_wtf import FlaskForm as _FlaskForm
from wtforms import BooleanField as _BooleanField


class FlaskForm(_FlaskForm):
    # CSRF Protection
    # https://wtforms.readthedocs.io/en/stable/csrf.html
    class Meta:
        csrf = False


class BooleanField(_BooleanField):
    # WTForms BooleanField Value And Validation
    # https://code.luasoftware.com/tutorials/python/wtforms-booleanfield-value-and-validation/

    def __init__(
        self,
        label=None,
        validators=None,
        false_values=(False, 'false', 'False', 'FALSE', 0, '0'),
        **kwargs
    ):
        # don't accept blank as False, so that default will trigger
        super().__init__(label, validators, false_values, **kwargs)

    def process_formdata(self, valuelist):
        if not valuelist or valuelist[0] == '' or valuelist[0] is None:
            self.data = self.default
        elif valuelist[0] in self.false_values:
            self.data = False
        else:
            self.data = True
