"""
Database connection handler.

Keeps a single persistent SQLite connection for the app's lifetime instead
of opening/closing per query, and enables WAL mode so invoice writes don't
block searches happening at the same time. This is the main thing that
keeps the app feeling fast under real use.
"""

import sqlite3
import os
from logic.config import DATABASE_PATH

DB_PATH = DATABASE_PATH

_connection = None


def get_connection():
    """Return the single persistent connection, creating it on first call."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL;")
        _connection.execute("PRAGMA foreign_keys=ON;")
    return _connection


def close_connection():
    """Close the connection cleanly — call this on app shutdown."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
