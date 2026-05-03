#!/usr/bin/env python3
"""Small CLI to set or reset the admin password.

Usage:
  python tools/admin_pass_cli.py set    # interactively set admin password
  python tools/admin_pass_cli.py rotate # rotate seeded usernames' passwords
"""
import sys
import getpass
import secrets
import logging
import database
import auth

logger = logging.getLogger('northshore.admin_cli')


def set_admin_password():
    conn = database.get_connection()
    try:
        cur = conn.execute("SELECT id, username FROM users WHERE username = 'admin'")
        row = cur.fetchone()
        if not row:
            print('No admin user found. Ensure the database has been initialised.')
            return
        while True:
            pwd = getpass.getpass('Enter new admin password: ')
            pwd2 = getpass.getpass('Confirm new admin password: ')
            if pwd != pwd2:
                print('Passwords do not match; try again.')
                continue
            if len(pwd) < 8:
                print('Use at least 8 characters.')
                continue
            break
        # update via auth.create_user-like logic but keeping username
        salt = secrets.token_hex(16)
        pwd_hash = auth._hash_password(pwd, salt.encode('utf-8'))
        database.safe_execute('UPDATE users SET password_hash = ?, salt = ? WHERE id = ?', (pwd_hash, salt, row['id']))
        print('Admin password updated.')
    finally:
        conn.close()


def rotate_passwords():
    auth.rotate_default_user_passwords()
    print('Rotated default seeded usernames passwords and wrote northshore_rotated_credentials.txt')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1].lower()
    if cmd == 'set':
        set_admin_password()
    elif cmd == 'rotate':
        rotate_passwords()
    else:
        print('Unknown command')


if __name__ == '__main__':
    main()
