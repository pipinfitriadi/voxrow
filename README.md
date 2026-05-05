<!--
Copyright (C) Pipin Fitriadi - All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 22 May 2025
-->

<!-- omit in toc -->
# VOXROW

[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)
[![PyPI - Python Version](https://img.shields.io/badge/python-3.12%2B-blue?logo=Python&logoColor=white)](https://www.python.org/downloads/release/python-3127/)
[![codecov](https://codecov.io/gh/pipinfitriadi/voxrow/graph/badge.svg?token=rTWjBKukUU)](https://codecov.io/gh/pipinfitriadi/voxrow)

- [Setup](#setup)
- [CI/CD](#cicd)

This repository serves as a centralized VOXROW's workspace,
providing structure and resources to support development activities.
It may include configuration files, environment setup, shared utilities
and documentation that help maintain consistency and streamline workflows
across projects or teams.

## Setup

Follow these steps the first time you use VS Code after cloning this git repository:

1. Create a _`.env`_ file based on [_`template.env`_](template.env)
   and set your environment values
2. Use the command <kbd>f1</kbd>, select `Tasks: Run Task`, and then choose `Preparation`
3. Use the command <kbd>f1</kbd>, select `Python: Select Interpreter`,
    and then choose _`./.venv/bin/python`_
4. Use the command <kbd>f1</kbd>, select `Tasks: Run Task`,
    and then choose `Python: Upgrade PIP`
5. Use the command <kbd>f1</kbd>, select `Tasks: Run Task`,
    and then choose `Python: Preparation`

## CI/CD

If you encounter a Code Quality error during the CI/CD process,
use the command <kbd>f1</kbd>, select `Tasks: Run Task`,
choose `CI/CD: Code Quality - Fixing`, and then run `git commit` and `git push`.
