import os
import sqlite3
from sqlite3 import Connection
from typing import List, Optional
import logging

BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, 'db')
DB_PATH = os.path.join(DB_DIR, 'northshore.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

logger = logging.getLogger('northshore.database')


def get_connection() -> Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def initialise_database() -> None:
    os.makedirs(DB_DIR, exist_ok=True)
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()
        logger.info('Created new database at %s', DB_PATH)
    execute_schema()


def execute_schema() -> None:
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError('schema.sql not found')
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn = get_connection()
    try:
        conn.executescript(sql)
        conn.commit()
        logger.info('Executed schema.sql')
    finally:
        conn.close()


def fetch_one(query: str, params: Optional[tuple] = None) -> Optional[sqlite3.Row]:
    conn = get_connection()
    try:
        cur = conn.execute(query, params or ())
        return cur.fetchone()
    finally:
        conn.close()


def fetch_all(query: str, params: Optional[tuple] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        cur = conn.execute(query, params or ())
        return cur.fetchall()
    finally:
        conn.close()


def safe_execute(query: str, params: Optional[tuple] = None) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(query, params or ())
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def safe_execute_many(query: str, seq_of_params: List[tuple]) -> None:
    conn = get_connection()
    try:
        conn.executemany(query, seq_of_params)
        conn.commit()
    finally:
        conn.close()
