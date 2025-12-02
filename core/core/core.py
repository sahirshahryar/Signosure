# core.py
# The main file for the signosure-core service.
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
from urllib.parse import quote_plus

from fastapi import FastAPI
from redis import Redis
from sqlalchemy import Engine
from tables import create_engine

from core import config, users

# Global database engine instance
engine = None

# Global Redis client instance
redis_client = None


def get_db() -> Engine:
    """
    Fetches a connection to the database, creating it if necessary.

    Supports SQLite, MySQL, and PostgreSQL databases based on the
    configuration in config.yaml.

    Returns:
        Engine: The SQLAlchemy database engine

    Raises:
        ValueError: If an unsupported database type is specified
    """
    global engine
    if engine is not None:
        return engine

    # Get database type from config
    db_type = config.get_config_value("database.type", str).lower()

    if db_type not in ["sqlite", "mysql", "postgresql"]:
        raise ValueError(
            f"Unsupported database type {db_type} "
            f"(must be one of 'sqlite', 'mysql', 'postgresql')"
        )

    # Build connection string based on database type
    if db_type == "sqlite":
        db_path = config.get_config_value("database.sqlite.path", str)
        connection_string = f"sqlite:///{db_path}"

    else:
        host = config.get_config_value(f"database.{db_type}.host", str)
        port = config.get_config_value(f"database.{db_type}.port", int)
        username = config.get_config_value(f"database.{db_type}.username", str)
        password = config.get_config_value(f"database.{db_type}.password", str)
        database = config.get_config_value(f"database.{db_type}.database", str)

        # URL-encode password to handle special characters
        encoded_password = quote_plus(password)
        protocol = "pymysql" if db_type == "mysql" else "psycopg2"
        connection_string = (
            f"{db_type}+{protocol}://{username}:{encoded_password}@"
            f"{host}:{port}/{database}"
        )

    engine = create_engine(connection_string)
    return engine


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

app.include_router(users.router, prefix="/core/users", tags=["users"])
app.include_router(config.router, prefix="/core/config", tags=["config"])
