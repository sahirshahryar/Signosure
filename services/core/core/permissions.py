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

from typing import Dict, List, Tuple

from core.config import get_config_value


# Generates bitwise masks, so as to make this file easier to work with.
# For example, LOGIN = 0b1, CREATE_USER = 0b10, UPDATE_USER_INFO = 0b100, ...
def gen_mask():
    mask = 1
    while True:
        yield mask
        mask <<= 1


# Unscoped permissions are permissions that apply to a user across the entire
# system.
UNSCOPED_GEN = gen_mask()

# Scoped permissions are permissions that apply to a user only in a specific
# context, e.g., within a dataset. We may not want a user to be able to
# contribute to or annotate ANY dataset across the entire system.
SCOPED_GEN = gen_mask()

# Lookup tables for unscoped permissions
UNSCOPED_PERMISSIONS: Dict[str, int] = dict()
UNSCOPED_PERMISSIONS_LOOKUP: Dict[int, str] = dict()

# Lookup tables for scoped permissions
SCOPED_PERMISSIONS: Dict[str, int] = dict()
SCOPED_PERMISSIONS_LOOKUP: Dict[int, str] = dict()


# Shorthand to generate a new unscoped permission and map it to a specific
# position in a bitmask
def unscoped(name: str) -> int:
    mask = next(UNSCOPED_GEN)
    UNSCOPED_PERMISSIONS[name] = mask
    UNSCOPED_PERMISSIONS_LOOKUP[mask] = name
    return mask


# Shorthand to generate a new scoped permission
def scoped(name: str) -> int:
    mask = next(SCOPED_GEN)
    SCOPED_PERMISSIONS[name] = mask
    SCOPED_PERMISSIONS_LOOKUP[mask] = name
    return mask


# Permission to log in. Without this permission, any attempt to
# log in as this user, even with the correct password, will fail.
LOGIN = unscoped("LOGIN")
"""
Allows a user to log in.
"""

SCOPED_READ = scoped("SCOPED_READ")
"""
Allows a user to read all data in a particular scope, including data that is
not their own. This permission is not required to collect or annotate data.
"""

SCOPED_WRITE = scoped("SCOPED_WRITE")
"""
Allows a user to modify all data in a particular scope. This permission
implicitly grants `SCOPED_READ` and is not required to collect or annotate
data.
"""

# SCOPED_CONTRIBUTE: Permission to contribute data in a specific scope.
SCOPED_CONTRIBUTE = scoped("SCOPED_CONTRIBUTE")
"""
Allows a user to collect data and upload it into datasets in this scope.
"""

# SCOPED_ANNOTATE: Permission to annotate videos.
SCOPED_ANNOTATE = scoped("SCOPED_ANNOTATE")
"""
Allows a user to annotate data in this scope.
"""


# Do not place any permissions after these statements, or the decode functions
# below will not work correctly.

UNSCOPED_UPPER_BOUND = next(UNSCOPED_GEN)
"""
All unscoped permission masks should have a value less than this.
"""

SCOPED_UPPER_BOUND = next(SCOPED_GEN)
"""
All scoped permission masks should have a value less than this.
"""


def encode(reference: Dict[str, int], permissions: List[str]) -> int:
    """
    Converts a list of named permissions to a binary mask, given a mapping of
    permissions to their binary masks.
    """
    composite = 0
    for permission in permissions:
        if permission not in reference:
            raise ValueError(f"Unknown permission '{permission}'")

        composite |= reference[permission]

    return composite


def encode_unscoped(permissions: List[str]) -> int:
    """
    Converts a list of unscoped permissions to a binary mask. For example,
    `encode_unscoped(['LOGIN'])` returns `0b1`.
    """
    return encode(UNSCOPED_PERMISSIONS, permissions)


def encode_scoped(permissions: List[str]) -> int:
    """
    Converts a list of scoped permissions to a binary mask. For example,
    `encode_scoped(['SCOPED_READ', 'SCOPED_ANNOTATE'])` returns `0b1001`.
    """
    return encode(SCOPED_PERMISSIONS, permissions)


def decode(reference: Dict[int, str], bound: int, composite: int) -> List[str]:
    """
    Converts a bitwise permission mask to a list of named permissions, given
    a map of bit masks to the permissions they represent.

    Params:
        - `reference`: (`Dict[int, str]`) a `dict()` mapping integer masks to
        named permissions.
        - `bound`: (`int`) the upper bound for all valid permissions.
        - `composite`: The permission mask to decode.

    Returns:
        (`List[str]`) the list of permissions in `reference` that are enabled
        in the permission mask.

    Raises:
        - `ValueError` if `composite > bound` (unrecognized permissions)
    """
    if composite > bound:
        error_bits = composite & (bound - 1)
        raise ValueError(f"Unmapped permissions at bits {error_bits:b}")

    mask = 0b1
    result: List[str] = list()
    while mask < bound:
        if mask & composite > 0:
            result.append(reference[mask])
        composite = composite & ~mask
        mask <<= 1

    return result


def decode_unscoped(composite: int) -> List[str]:
    """
    Converts a bitwise permission mask into a list of the unscoped permissions
    that it represents. For example, `decode_unscoped(0b1)` returns
    `['LOGIN']`.
    """
    return decode(UNSCOPED_PERMISSIONS_LOOKUP, UNSCOPED_UPPER_BOUND, composite)


def decode_scoped(composite: int) -> List[str]:
    """
    Converts a bitwise permission mask into a list of the scoped permissions
    that it represents. For example, `decode_scoped(0b11000)` returns
    `['SCOPED_CONTRIBUTE', 'SCOPED_ANNOTATE']`.
    """
    return decode(SCOPED_PERMISSIONS_LOOKUP, SCOPED_UPPER_BOUND, composite)


def get_default_permissions(category: str) -> Tuple[int, int]:
    """
    Loads the default permissions for a given category. See
    `core/resources/config.yaml -> permissions` for a list of
    possible values.
    """
    try:
        unscoped_list = get_config_value(
            f"permissions.{category}.unscoped", List[str]
        )
        unscoped = encode_unscoped(unscoped_list)
    except KeyError:
        # Note: encode_unscoped can raise ValueError for unknown
        # permissions; these will be passed through
        unscoped = 0

    try:
        scoped_list = get_config_value(
            f"permissions.{category}.scoped", List[str]
        )
        scoped = encode_scoped(scoped_list)
    except KeyError:
        scoped = 0

    return (unscoped, scoped)
