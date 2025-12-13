"""
An list of the permissions assignable to a user, plus helper functions for
permissions.
"""

# permissions.py
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

from enum import Flag, auto
from typing import List, Set, Tuple, Type, TypeVar

from core.config import get_config_value

# Type variable for generic encode/decode functions
P = TypeVar("P", bound=Flag)


def decode_flag_enum(cls: Type[P], flag: P, exclusions: Set[P]) -> List[str]:
    """
    Decodes a Flag enum value into a list of member names.

    Params:
    - `cls`: The Flag enum class.
    - `flag`: The flag value to decode.
    - `exclusions`: (`Set`) the values of the enum to exclude from decoding.
      Useful for special values, like `ALL`, which would be very
      unhelpful to display.

    Returns:
        (`List[str]`) the list of member names that are enabled in `flag`.
    """
    if flag.value == 0:
        return ["NONE"]

    return [
        member.name
        for member in cls
        if member.name is not None
        and member in flag
        and member not in exclusions
    ]


def encode_flag_enum(cls: Type[P], flags: Set[str], exclusions: Set[P]) -> P:
    result = 0

    for flag in cls:
        if flag in exclusions or flag.name is None:
            continue

        if flag.name in flags:
            result |= flag.value

    return cls(result)


class UnscopedPermission(Flag):
    """
    Permissions that apply to a user across the entire system.
    """

    NONE = 0
    LOGIN = auto()
    """
    Allows a user to log in. Without this permission, any attempt to log in
    as this user, even with the correct password, will fail.
    """

    ALL = LOGIN

    @classmethod
    def decode(cls, flag: "UnscopedPermission") -> List[str]:
        return decode_flag_enum(
            cls, flag, {UnscopedPermission.NONE, UnscopedPermission.ALL}
        )

    @classmethod
    def encode(cls, flags: Set[str]) -> "UnscopedPermission":
        return encode_flag_enum(
            cls, flags, {UnscopedPermission.NONE, UnscopedPermission.ALL}
        )


class ScopedPermission(Flag):
    """
    Permissions that apply to a user only within a specific context, e.g.,
    within a dataset. We may not want a user to be able to contribute to or
    annotate ANY dataset across the entire system.
    """

    NONE = 0

    RESEARCHER = auto()
    """
    Allows a user to view a dataset, run processing tasks on that dataset, and
    edit some limited properties of a dataset (such as prompts).
    """

    DATASET_EDITOR = auto()
    """
    Allows a user to modify all data in a particular scope. This permission
    implicitly grants `READ` and is not required to collect or annotate data.
    """

    CONTRIBUTE = auto()
    """
    Allows a user to collect data and upload it into datasets in this scope.
    """

    ANNOTATE = auto()
    """
    Allows a user to annotate data in this scope.
    """

    VISUALIZE_DATA = auto()
    """
    Allows a user to view data visualizations.
    """

    ASK_QUESTIONS = auto()
    """
    Allows a user to message the researchers.
    """

    ANSWER_QUESTIONS = auto()
    """
    Allows a user to answer researchers.
    """

    ALL = (
        RESEARCHER
        | DATASET_EDITOR
        | CONTRIBUTE
        | ANNOTATE
        | VISUALIZE_DATA
        | ASK_QUESTIONS
        | ANSWER_QUESTIONS
    )

    WEB_VISIBILITY = (
        RESEARCHER
        | DATASET_EDITOR
        | ANNOTATE
        | VISUALIZE_DATA
        | ASK_QUESTIONS
        | ANSWER_QUESTIONS
    )

    @classmethod
    def decode(cls, flag: "ScopedPermission"):
        return decode_flag_enum(
            cls,
            flag,
            {
                ScopedPermission.NONE,
                ScopedPermission.ALL,
                ScopedPermission.WEB_VISIBILITY,
            },
        )

    @classmethod
    def encode(cls, flags: Set[str]):
        return encode_flag_enum(
            cls,
            flags,
            {
                ScopedPermission.NONE,
                ScopedPermission.ALL,
                ScopedPermission.WEB_VISIBILITY,
            },
        )


def get_default_permissions(
    category: str,
) -> Tuple[UnscopedPermission, ScopedPermission]:
    """
    Loads the default permissions for a given category. See
    `core/resources/config.yaml -> permissions` for a list of
    possible values.

    Params:
        - `category`: The permission category to load (e.g., 'default')

    Returns:
        (`Tuple[int, int]`) a tuple of (unscoped_mask, scoped_mask)
    """
    try:
        unscoped_list = get_config_value(
            f"permissions.{category}.unscoped", List[str]
        )
        unscoped = UnscopedPermission.encode(set(unscoped_list))
    except KeyError:
        unscoped = UnscopedPermission.NONE

    try:
        scoped_list = get_config_value(
            f"permissions.{category}.scoped", List[str]
        )
        scoped = ScopedPermission.encode(set(scoped_list))
    except KeyError:
        scoped = ScopedPermission.NONE

    return (unscoped, scoped)
