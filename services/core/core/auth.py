"""
Utility functions for session-based authentication and authorization.
"""

# auth.py
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
from typing import Callable, Optional

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlmodel import Session

from core.core import get_redis
from core.tables import User


def create_session(user_id: int, response: Response) -> str:
    """
    Creates a new session for a user and sets the session cookie.

    TODO: Implement this function to:
    1. Generate a secure random session ID (use secrets.token_urlsafe)
    2. Store session data in Redis with user_id and metadata (created_at, last_accessed)
    3. Set session expiration in Redis (e.g., 7 days)
    4. Set httponly, secure, and samesite cookie in the response
    5. Return the session ID
    """
    raise NotImplementedError


def get_session(session_id: str) -> Optional[dict]:
    """
    Retrieves session data from Redis.

    TODO: Implement this function to:
    1. Look up the session ID in Redis
    2. If found, parse and return the session data as a dict
    3. If not found or expired, return None
    4. Update last_accessed timestamp
    """
    raise NotImplementedError


def refresh_session(session_id: str) -> bool:
    """
    Extends the expiration time of an existing session.

    TODO: Implement this function to:
    1. Check if session exists in Redis
    2. If exists, extend the TTL (time-to-live)
    3. Return True if successful, False otherwise
    """
    raise NotImplementedError


def delete_session(session_id: str) -> bool:
    """
    Deletes a session from Redis (logout).

    TODO: Implement this function to:
    1. Remove the session from Redis
    2. Return True if successful, False if session didn't exist
    """
    raise NotImplementedError


def delete_all_user_sessions(user_id: int) -> int:
    """
    Deletes all sessions for a specific user (e.g., for password reset).

    TODO: Implement this function to:
    1. Find all session keys for the given user_id
    2. Delete all matching sessions from Redis
    3. Return the count of deleted sessions

    Note: May require maintaining a user_id -> session_ids mapping
    or using Redis SCAN with pattern matching
    """
    raise NotImplementedError


async def get_current_user(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
) -> Optional[User]:
    """
    Validates a session cookie and returns the User object.

    TODO: Implement this function to:
    1. Check if session_id cookie exists
    2. Retrieve session data from Redis using get_session()
    3. Extract user_id from session data
    4. Look up the user in the database
    5. Return the User object (or raise HTTPException 401 if invalid)
    """
    raise NotImplementedError


async def require_current_user(
    user: Optional[User] = Depends(get_current_user),
):
    """
    Requires the user to be logged in, automatically failing if not authorized.
    """
    if user is not None:
        return user

    raise HTTPException(401)


async def get_current_active_user(
    current_user: User = Depends(require_current_user),
) -> User:
    """
    Ensures the user making the request is logged in with an account that has
    a validated email.
    """
    if current_user.validated:
        return current_user

    raise HTTPException(403)


async def get_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Ensures the user making the request is logged in as an administrator.
    """
    if current_user.admin:
        return current_user

    raise HTTPException(403)


async def get_user_with_permission(unscoped: int = 0) -> Callable:
    """
    Verifies that the user has the given permissions (provided as a mask).
    Used with `Depends()`. For example:

    ```py
    async def modify_user(
        user: User = Depends(get_user_with_permission(MODIFY_USER))
    ):
        pass
    ```
    """

    def helper(user: User = Depends(get_current_user)):
        if not user.has_permissions(unscoped):
            raise HTTPException(403)
        return user

    return helper
