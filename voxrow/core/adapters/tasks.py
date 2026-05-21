#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

from typing import ParamSpec, Protocol, runtime_checkable

from ..domain import value_objects

P: ParamSpec = ParamSpec("P")


@runtime_checkable
class Task(Protocol[P]):
    def __call__(
        self,
        *args: P.args,
        settings: value_objects.Settings,
        **kwargs: P.kwargs,
    ) -> any: ...
