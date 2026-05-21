#!/usr/bin/env python3

# Copyright (C) Pipin Fitriadi - All Rights Reserved

# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 21 May 2026

from functools import wraps
from inspect import Parameter, Signature, signature

from pydantic import validate_call
from typer import Context

from ..adapters.tasks import Task
from ..domain import value_objects


@validate_call(config=value_objects.CONFIG_DICT)
def inject_settings(task: Task) -> Task:
    keyword: str = "settings"

    @wraps(task)
    def wrapper(
        context: Context,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> any:  # pragma: no cover
        kwargs.pop(keyword, None)

        return task(*args, settings=context.obj, **kwargs)

    wrapper.__signature__ = Signature(
        parameters=(
            Parameter(
                "context",
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Context,
            ),
            *(
                param
                for name, param in signature(task).parameters.items()
                if name != keyword
            ),
        )
    )

    return wrapper
