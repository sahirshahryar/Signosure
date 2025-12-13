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
import json
import secrets
import time
from typing import Callable, Optional

from fastapi import Cookie, Depends, HTTPException, Response, status

from core.config import get_config_value
from core.core import get_redis
from core.mongodb import User

# Session configuration
SESSION_EXPIRATION = 7 * 24 * 60 * 60  # 7 days in seconds
SESSION_PREFIX = "session:"
USER_SESSIONS_PREFIX = "user_sessions:"


def create_session(user_id: str, response: Response) -> str:
    """
    Creates a new session for a user and sets the session cookie.

    Params:
        `user_id`: (`str`) the MongoDB ObjectId of the user (as string)
        `response`: (`Response`) FastAPI Response object to set the cookie

    Returns:
        (`str`) the generated session ID
    """
    redis = get_redis()

    # Generate a secure random session ID
    session_id = secrets.token_urlsafe(32)

    # Create session data
    current_time = int(time.time() * 1000)  # Milliseconds since epoch
    session_data = {
        "user_id": user_id,
        "created_at": current_time,
        "last_accessed": current_time,
    }

    # Store session in Redis with expiration
    session_key = f"{SESSION_PREFIX}{session_id}"
    redis.setex(session_key, SESSION_EXPIRATION, json.dumps(session_data))

    # Track this session for the user (for bulk deletion)
    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id}"
    redis.sadd(user_sessions_key, session_id)
    redis.expire(user_sessions_key, SESSION_EXPIRATION)

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=SESSION_EXPIRATION,
        httponly=True,
        secure=True,  # Requires HTTPS in production
        samesite="lax",
    )

    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """
    Retrieves session data from Redis.

    Params:
        `session_id`: (`str`) the session ID to look up

    Returns:
        (`Optional[dict]`) session data as a dict, or `None` if not found or
        expired
    """
    redis = get_redis()

    session_key = f"{SESSION_PREFIX}{session_id}"
    session_json = redis.get(session_key)

    if not session_json:
        return None

    # Parse session data
    session_data = json.loads(session_json)  # type: ignore

    # Update last_accessed timestamp
    session_data["last_accessed"] = int(time.time() * 1000)
    redis.setex(session_key, SESSION_EXPIRATION, json.dumps(session_data))

    return session_data


def refresh_session(session_id: str) -> bool:
    """
    Extends the expiration time of an existing session.

    Params:
        `session_id`: (`str`) the session ID to refresh

    Returns:
        (`bool`) `True` if successful, `False` if session doesn't exist
    """
    redis = get_redis()

    session_key = f"{SESSION_PREFIX}{session_id}"

    # Check if session exists
    if not redis.exists(session_key):
        return False

    # Extend the TTL
    redis.expire(session_key, SESSION_EXPIRATION)

    return True


def delete_session(session_id: str) -> bool:
    """
    Deletes a session from Redis (logout).

    Params:
        `session_id`: (`str`) the session ID to delete

    Returns:
        (`bool`) `True` if successful, `False` if session didn't exist
    """
    redis = get_redis()

    session_key = f"{SESSION_PREFIX}{session_id}"

    # Get session data to find user_id before deletion
    session_json = redis.get(session_key)
    if session_json:
        session_data = json.loads(session_json)  # type: ignore
        user_id = session_data.get("user_id")

        # Remove from user's session set
        if user_id:
            user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id}"
            redis.srem(user_sessions_key, session_id)

    # Delete the session
    deleted_count: int = redis.delete(session_key)  # type: ignore

    return deleted_count > 0


def delete_all_user_sessions(user_id: str) -> int:
    """
    Deletes all sessions for a specific user (e.g., for password reset).

    Params:
        `user_id`: (`str`) the user's MongoDB ObjectId (as string)

    Returns:
        (`int`) the count of deleted sessions
    """
    redis = get_redis()

    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id}"

    # Get all session IDs for this user
    session_ids = redis.smembers(user_sessions_key)

    if not session_ids:
        return 0

    # Delete all session keys
    deleted_count = 0
    for session_id in session_ids:  # type: ignore
        session_key = f"{SESSION_PREFIX}{session_id}"
        result: int = redis.delete(session_key)  # type: ignore
        if result > 0:
            deleted_count += 1

    # Delete the user sessions set
    redis.delete(user_sessions_key)

    return deleted_count


async def get_current_user(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
) -> Optional[User]:
    """
    Validates a session cookie and returns the User object.

    Params:
        `session_id`: (`Optional[str]`) the session ID from the cookie

    Returns:
        (`Optional[User]`) the User object if valid session, `None` otherwise
    """
    if not session_id:
        return None

    # Retrieve session data from Redis
    session_data = get_session(session_id)
    if not session_data:
        return None

    # Extract user_id from session
    user_id = session_data.get("user_id")
    if not user_id:
        return None

    # Look up the user in MongoDB
    user = await User.get(user_id)

    return user


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
