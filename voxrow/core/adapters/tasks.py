#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

from typing import Protocol, runtime_checkable

from ..domain import value_objects


@runtime_checkable
class Task(Protocol[value_objects.Param]):
    def __call__(
        self,
        settings: value_objects.Settings,
        *args: value_objects.Param.args,
        **kwargs: value_objects.Param.kwargs,
    ) -> any: ...
