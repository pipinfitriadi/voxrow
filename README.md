<!--
Copyright (C) Pipin Fitriadi - All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Pipin Fitriadi <pipinfitriadi@gmail.com>, 22 May 2025
-->

<!-- omit in toc -->
# Python

[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)
[![PyPI - Python Version](https://img.shields.io/badge/python-3.13%2B-blue?logo=Python&logoColor=white)](https://www.python.org/downloads/release/python-3131/)

- [Setup](#setup)
- [CI/CD](#cicd)

This repository serves as a centralized Python's workspace,
providing structure and resources to support development activities.
It may include configuration files, environment setup, shared utilities
and documentation that help maintain consistency and streamline workflows
across projects or teams.

## Setup

Follow these steps the first time you use VS Code after cloning this git repository:

1. Change `name` value in [pyproject.toml](pyproject.toml) to your project name
2. Create a _`.env`_ file based on [_`template.env`_](template.env)
   and set your environment values
3. Use the command <kbd>command | ctrl</kbd> + <kbd>shift</kbd> + <kbd>P</kbd>,
    select `Tasks: Run Task`, and then choose `Preparation`
4. Use the command <kbd>command | ctrl</kbd> + <kbd>shift</kbd> + <kbd>P</kbd>,
    select `Python: Select Interpreter`, and then choose _`./.venv/bin/python`_
5. Use the command <kbd>command | ctrl</kbd> + <kbd>shift</kbd> + <kbd>P</kbd>,
    select `Tasks: Run Task`, and then choose `Python: Preparation`

## CI/CD

If you encounter a Code Quality error during the CI/CD process,
use the command <kbd>command | ctrl</kbd> + <kbd>shift</kbd> + <kbd>P</kbd>,
select `Tasks: Run Task`, choose `CI/CD: Code Quality - Fixing`,
and then run `git commit` and `git push`.
