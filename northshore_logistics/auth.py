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


def ensure_default_users() -> None:
    # Ensure roles exist. Do NOT create users with hard-coded passwords.
    roles = ['Admin', 'Manager', 'Warehouse Staff', 'Driver', 'Customer Service']
    existing = {r['name'] for r in database.fetch_all('SELECT name FROM roles')}
    for r in roles:
        if r not in existing:
            database.safe_execute('INSERT INTO roles (name) VALUES (?)', (r,))
    # If there are no users at all, create a single admin with a generated password
    # and write credentials to a local file outside version control.
    users_exist = database.fetch_one('SELECT id FROM users LIMIT 1')
    if not users_exist:
        _create_initial_admin()
    else:
        # If there are existing users, rotate any common seeded usernames' passwords
        try:
            rotate_default_user_passwords()
        except Exception:
            logger.exception('Error rotating default user passwords')


def _create_initial_admin() -> None:
    try:
        rows = database.fetch_all('SELECT id, name FROM roles')
        role_map = {r['name']: r['id'] for r in rows}
        admin_role = role_map.get('Admin')
        if admin_role is None:
            logger.error('Admin role not found when creating initial admin')
            return
        username = 'admin'
        # Generate a strong random password
        password = secrets.token_urlsafe(16)
        create_user(username, password, admin_role, display_name='Administrator')
        # Write credentials to a local file for the operator. This file should be kept
        # out of version control (.gitignore) and removed after first use.
        cred_path = database.get_db_path() if hasattr(database, 'get_db_path') else 'northshore_local_credentials.txt'
        try:
            # If database exposes a project dir, write next to DB; otherwise use cwd file
            if isinstance(cred_path, str) and cred_path.endswith('.db'):
                cred_file = cred_path.replace('.db', '.credentials.txt')
            else:
                cred_file = 'northshore_local_credentials.txt'
            with open(cred_file, 'w', encoding='utf-8') as f:
                f.write(f'Initial admin username: {username}\n')
                f.write(f'Initial admin password: {password}\n')
            logger.info('Wrote initial admin credentials to %s', cred_file)
        except Exception:
            logger.exception('Failed to write initial admin credentials to file')
    except Exception:
        logger.exception('Failed to create initial admin')


def rotate_default_user_passwords() -> None:
    """If common seeded usernames exist, rotate their passwords to random values
    and write the new credentials to a local file. This helps remove predictable
    credentials that may have been present in earlier seeds/README."""
    defaults = ['admin', 'manager', 'warehouse', 'driver', 'service']
    rotated = []
    try:
        rows = database.fetch_all('SELECT id, username FROM users WHERE username IN (?,?,?,?,?)', tuple(defaults))
        if not rows:
            return
        for r in rows:
            new_pwd = secrets.token_urlsafe(16)
            # update password for user id
            salt = secrets.token_hex(16)
            pwd_hash = _hash_password(new_pwd, salt.encode('utf-8'))
            database.safe_execute('UPDATE users SET password_hash = ?, salt = ? WHERE id = ?', (pwd_hash, salt, r['id']))
            rotated.append((r['username'], new_pwd))
        # write rotated credentials to a local file
        try:
            cred_file = 'northshore_rotated_credentials.txt'
            with open(cred_file, 'w', encoding='utf-8') as f:
                for u, p in rotated:
                    f.write(f'{u}:{p}\n')
            logger.info('Wrote rotated credentials to %s', cred_file)
        except Exception:
            logger.exception('Failed to write rotated credentials')
    except Exception:
        logger.exception('Failed to rotate default user passwords')
