# config.py
# Handles loading configuration values for the core service.
#
# This file is part of Signosure.
#
# Copyright (c) 2025 Georgia Institute of Technology
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import os
from pathlib import Path
from typing import Any, Type, TypeVar, Union, cast

import yaml
from fastapi import APIRouter, HTTPException

T = TypeVar("T", int, str, bool, dict, list)
ConfigValue = Union[int, str, bool, dict, list]

CONFIG_PATH_ENV = "SIGNOSURE_CONFIG"
"""
The name of the environment variable whose value points to the config.yaml file.
For example, we may start the core service with the environment variable
`SIGNOSURE_CONFIG=path/to/config.yaml`.
"""

BASE_CONFIG_PATH = "./resources/config.yaml"
"""
The file path to the base configuration file. All configuration values must be
defined and assigned a default value in this file, as `merge_config()` will
ignore any keys not included in this file when applying an override config.
"""

router = APIRouter()

config_loaded = False
config = dict()


def merge_config(base: dict, override: dict) -> None:
    """
    Merges two nested dictionaries such that only values in the `base` dictionary
    can be overwritten by values in `override`. For example, given
    `base     = { a: { b: True, c: 20, d: { f: True } } }` and
    `override = { a: { b: False, e: { f: False } }, g: 10 }`, the
    result of this function is

    ```
    {
      a: {
        b: False,     // Overwritten by value in `override`
        c: 20,        // Preserved because it exists in `base`
        d: {
          f: True     // Preserved because `f` in `override` is under `e`,
                      // not `d`
        }
      }
                      // `g` not included because no match in `base`
    }
    ```
    """
    for key, value in override.items():
        if key not in base:
            continue

        if isinstance(value, dict) and isinstance(base[key], dict):
            merge_config(base[key], value)
        else:
            base[key] = value


def load_config_file():
    """
    Loads the system configuration. This function loads the base configuration
    file located at `BASE_CONFIG_PATH`. If an override configuration was
    passed in as an environment variable (see `CONFIG_PATH_ENV`), then that
    config file will loaded and merged with the base configuration.
    """
    global config_loaded, config

    with open(BASE_CONFIG_PATH, "r") as base_f:
        config = yaml.safe_load(base_f)

    override_path = os.environ.get(CONFIG_PATH_ENV)
    if override_path and Path(override_path).exists():
        with open(override_path, "r") as f:
            overrides = yaml.safe_load(f)

        merge_config(config, overrides)

    config_loaded = True


def get_key(obj: dict, key: str):
    """
    Navigates to a nested object in a `dict()` using dot notation. For example,
    in the below object, `get_key(obj, "a.b.c")` returns `5`:

    ```
    obj = {
        'a': {
            'b': {
                'c': 5
            },
            'd': 10
        }
    }
    ```

    Raises:
        `KeyError` if any object along the path does not exist
    """
    keys = key.split(".")
    nested = obj
    for k in keys:
        if not isinstance(nested, dict) or k not in nested:
            raise KeyError(f"Configuration key {key} not found")
        nested = config[k]
    return nested


def get_config_value(key: str, expected_type: Type[T]) -> T:
    """
    Gets the configuration value at the specified path, coercing it to the
    expected type.

    Params:
        - `key`: (`str`) the key in dot notation (see `get_key()`).
        - `expected_type`: (`Type[T]`) the expected type of the object.

    Returns:
        (`T`) the value at that path in the configuration.

    Raises:
        - `KeyError` if the configuration requested does not exist
        - `TypeError` if the configuration value doesn't match `expected_type`
    """
    if not config_loaded:
        load_config_file()

    result = get_key(config, key)
    if not isinstance(result, expected_type):
        raise TypeError(
            f"Configuration key {key} has type {type(result).__name__}, "
            f"expected {expected_type.__name__}"
        )

    return cast(T, result)


@router.get(path="/fetch")
async def get_config(key: str) -> Any:
    """
    `GET`s the configuration value at the expected path.

    Params:
        - `key`: (`str`) the key in dot notation (see `get_key()`).

    Returns:
        (`Any`) the value at that path in the configuration

    Raises:
        - `HTTPException` if the configuration value at that path is not found
    """
    if not config_loaded:
        load_config_file()

    try:
        return get_key(config, key)
    except KeyError:
        raise HTTPException(
            status_code=400, detail=f"Configuration key {key} not found"
        )
