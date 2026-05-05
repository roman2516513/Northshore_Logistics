import hashlib
import secrets
from typing import Optional, Tuple
from datetime import datetime

import database
import logging

logger = logging.getLogger('northshore.auth')

PBKDF2_ITERATIONS = 100_000


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return dk.hex()


def create_user(username: str, password: str, role_id: int, display_name: Optional[str] = None) -> int:
    salt = secrets.token_hex(16)
    pwd_hash = _hash_password(password, salt.encode('utf-8'))
    now = datetime.utcnow().isoformat()
    query = 'INSERT INTO users (username, display_name, role_id, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?, ?)'
    try:
        uid = database.safe_execute(query, (username, display_name or username, role_id, pwd_hash, salt, now))
        logger.info('Created user %s', username)
        return uid
    except Exception as e:
        logger.exception('Failed to create user %s: %s', username, e)
        raise


def verify_user(username: str, password: str) -> Optional[Tuple[int, str, int]]:
    row = database.fetch_one('SELECT id, password_hash, salt, role_id FROM users WHERE username = ?', (username,))
    if not row:
        logger.info('Login failed: unknown user %s', username)
        return None
    salt = row['salt']
    expect = row['password_hash']
    got = _hash_password(password, salt.encode('utf-8'))
    if secrets.compare_digest(expect, got):
        logger.info('User %s authenticated', username)
        return (row['id'], username, row['role_id'])
    logger.info('Invalid password for %s', username)
    return None


def update_password(user_id: int, new_password: str) -> None:
    """Update a user's password by user id."""
    try:
        salt = secrets.token_hex(16)
        pwd_hash = _hash_password(new_password, salt.encode('utf-8'))
        database.safe_execute('UPDATE users SET password_hash = ?, salt = ? WHERE id = ?', (pwd_hash, salt, user_id))
        logger.info('Updated password for user id %s', user_id)
    except Exception:
        logger.exception('Failed to update password for user id %s', user_id)


def ensure_default_users() -> None:
    roles = ['Admin', 'Manager', 'Warehouse Staff', 'Driver', 'Customer Service']
    existing = {r['name'] for r in database.fetch_all('SELECT name FROM roles')}
    for r in roles:
        if r not in existing:
            database.safe_execute('INSERT INTO roles (name) VALUES (?)', (r,))
    rows = database.fetch_all('SELECT id, name FROM roles')
    role_map = {r['name']: r['id'] for r in rows}

    defaults = [
        ('admin', 'Admin123!', 'Admin'),
        ('manager', 'Manager123!', 'Manager'),
        ('warehouse', 'Warehouse123!', 'Warehouse Staff'),
        ('driver', 'Driver123!', 'Driver'),
        ('service', 'Service123!', 'Customer Service')
    ]
    for username, pwd, role_name in defaults:
        exists = database.fetch_one('SELECT id FROM users WHERE username = ?', (username,))
        if not exists:
            create_user(username, pwd, role_map[role_name], display_name=username.capitalize())
