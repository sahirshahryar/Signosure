"""
The main file for the `signosure-core` service.
"""

# core.py
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
from contextlib import asynccontextmanager
from urllib.parse import quote_plus

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis

from core import collections, config, users

# Global database engine instance
engine = None

# Global MongoDB client instance
mongodb_client = None
mongodb_initialized = False

# Global Redis client instance
redis_client = None


async def init_mongodb() -> None:
    """
    Initializes the MongoDB connection and Beanie ODM.

    Raises:
        ConnectionError: If unable to connect to MongoDB
        ValueError: If MongoDB configuration is invalid
    """
    global mongodb_client, mongodb_initialized

    if mongodb_initialized:
        return

    # Get MongoDB configuration
    try:
        host = config.get_config_value("mongodb.host", str)
        port = config.get_config_value("mongodb.port", int)
        database = config.get_config_value("mongodb.database", str)
    except KeyError as e:
        raise ValueError(f"Missing MongoDB configuration: {e}")

    # Username and password are optional for local development
    try:
        username = config.get_config_value("mongodb.username", str)
        password = config.get_config_value("mongodb.password", str)
        # Build authenticated connection string
        connection_string = (
            f"mongodb://{username}:{quote_plus(password)}@{host}:{port}"
        )
    except KeyError:
        # No authentication for local development
        connection_string = f"mongodb://{host}:{port}"

    # Create MongoDB client
    try:
        mongodb_client = AsyncIOMotorClient(connection_string)
        db = mongodb_client[database]

        # Test connection
        await mongodb_client.admin.command("ping")

        # Initialize Beanie with all document models
        await init_beanie(
            database=db,  # type: ignore
            document_models=[
                collections.User,
                collections.Dataset,
                collections.Video,
                collections.Prompt,
                collections.PermissionScope,
            ],
        )

        mongodb_initialized = True

    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")


def get_redis() -> Redis:
    """
    Fetches a connection to Redis, creating it if necessary.

    Redis is used for session storage and caching.

    Returns:
        Redis: The Redis client instance

    Raises:
        ConnectionError: If unable to connect to Redis
    """
    global redis_client
    if redis_client is not None:
        return redis_client

    # Get Redis configuration
    host = config.get_config_value("redis.host", str)
    port = config.get_config_value("redis.port", int)
    db = config.get_config_value("redis.db", int)

    # Password is optional
    try:
        password = config.get_config_value("redis.password", str)
    except KeyError:
        password = None

    # Create Redis client with connection pooling
    redis_client = Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True,  # Automatically decode responses to strings
        socket_connect_timeout=5,
        socket_timeout=5,
    )

    # Test connection
    try:
        redis_client.ping()
    except Exception as e:
        raise ConnectionError(f"Failed to connect to Redis: {e}")

    return redis_client


app = FastAPI()


@asynccontextmanager
async def startup_event():
    """Initialize MongoDB connection on application startup."""
    await init_mongodb()
    yield


app.include_router(users.router, prefix="/core/users", tags=["users"])
app.include_router(config.router, prefix="/core/config", tags=["config"])
