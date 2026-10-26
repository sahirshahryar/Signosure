"""
An list of the permissions assignable to a user, plus helper functions for
permissions.
"""

# permissions.py
# This file is part of Signosure.
#
# Copyright (c) 2026 Georgia Institute of Technology
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


def decode_flag_enum(cls: Type[P], flag: P) -> List[str]:
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
        # Only include enum members with 1 set bit:
        and member.value & (member.value - 1) == 0
        and member in flag
    ]


def encode_flag_enum(cls: Type[P], flags: Set[str]) -> P:
    result = 0

    for flag in cls:
        # Only consider enum members with 1 set bit
        if flag.value & (flag.value - 1) != 0 or flag.name is None:
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
        return decode_flag_enum(cls, flag)

    @classmethod
    def encode(cls, flags: Set[str]) -> "UnscopedPermission":
        return encode_flag_enum(cls, flags)


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

    EDIT_DATASET = auto()
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
    Allows a user to annotate data in this scope. With this permission, users
    can annotate only the videos that have been explicitly assigned to them.
    """

    OTHER_ANNOTATIONS_READ = auto()
    """
    Allows a user to see others' annotations on a clip. These include ratings,
    re-trims, and comments. Disabling this can be useful to make sure reviewers
    aren't influenced by prior annotations.
    """

    OTHER_ANNOTATIONS_WRITE = auto()
    """
    Allows a user to modify others' annotations on a clip, including ratings,
    re-trims, and comments.
    """

    ANNOTATE_UNASSIGNED_READ = auto()
    """
    Allows a user to view annotations for clips that are not assigned to them.
    """

    ANNOTATE_UNASSIGNED_WRITE = auto()
    """
    Allows a user to annotate clips that have not been assigned to them.
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
        | EDIT_DATASET
        | CONTRIBUTE
        | ANNOTATE
        | VISUALIZE_DATA
        | ASK_QUESTIONS
        | ANSWER_QUESTIONS
    )

    WEB_VISIBILITY = (
        RESEARCHER
        | EDIT_DATASET
        | ANNOTATE
        | VISUALIZE_DATA
        | ASK_QUESTIONS
        | ANSWER_QUESTIONS
    )
    """
    A mask containing all the permissions that are used to determine whether
    the various navigation tabs in the Signosure web UI are visible. When
    passing permission data to SvelteKit, the user's full set of scoped
    permissions should be ANDed with this value, as the other permissions in a
    user's permission mask do not need to be visible to SvelteKit.
    """

    VIEW_DATASET = RESEARCHER | EDIT_DATASET
    """
    This permission controls whether a user should be able to see a particular
    dataset in the sidebar of the `Datasets` view.
    """

    VIEW_COLLECTION = RESEARCHER | EDIT_DATASET
    """
    This permission controls whether a user should be able to monitor users'
    collection progress (and view individual videos) on a specific dataset
    in the `Collection` view.
    """

    VIEW_PROCESSING = RESEARCHER
    """
    This permission controls whether a user can view a dataset in the
    `Processing` view.
    """

    VIEW_ANNOTATION = RESEARCHER | ANNOTATE
    """
    This permission controls whether a user can view a dataset in the
    `Annotation` view.
    """

    VIEW_VISUALIZATION = RESEARCHER | VISUALIZE_DATA
    VIEW_USERS = RESEARCHER
    VIEW_QUESTIONS = ASK_QUESTIONS | ANSWER_QUESTIONS

    @classmethod
    def decode(cls, flag: "ScopedPermission"):
        return decode_flag_enum(cls, flag)

    @classmethod
    def encode(cls, flags: Set[str]):
        return encode_flag_enum(cls, flags)


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
            f"permissions.{category}.unscoped", List
        )
        unscoped = UnscopedPermission.encode(set(unscoped_list))
    except KeyError:
        unscoped = UnscopedPermission.NONE

    try:
        scoped_list = get_config_value(f"permissions.{category}.scoped", List)
        scoped = ScopedPermission.encode(set(scoped_list))
    except KeyError:
        scoped = ScopedPermission.NONE

    return (unscoped, scoped)
