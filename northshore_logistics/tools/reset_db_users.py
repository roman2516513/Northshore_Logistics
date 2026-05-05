#!/usr/bin/env python3
"""Reset users table and reseed default users with hard-coded passwords.
Backs up the DB file to northshore.db.bak before modifying.
"""
import os
import sys
import shutil
# Ensure project root is on sys.path so imports like `database` and `auth` resolve
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

import database
import auth

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'northshore.db')
DB_PATH = os.path.normpath(DB_PATH)

print('DB path:', DB_PATH)
# Backup
if os.path.exists(DB_PATH):
    bak = DB_PATH + '.bak'
    shutil.copy2(DB_PATH, bak)
    print('Backed up DB to', bak)
else:
    print('No existing DB to back up')

# Delete all users
conn = database.get_connection()
try:
    print('Deleting all users...')
    conn.execute('DELETE FROM users')
    conn.commit()
    print('Deleted users table rows')
finally:
    conn.close()

# Reseed
print('Reseeding default users...')
auth.ensure_default_users()

# Verify
defaults = [
    ('admin', 'Admin123!'),
    ('manager', 'Manager123!'),
    ('warehouse', 'Warehouse123!'),
    ('driver', 'Driver123!'),
    ('service', 'Service123!')
]
print('\nVerifying credentials:')
for u, p in defaults:
    ok = auth.verify_user(u, p)
    print(f"{u}: {'OK' if ok else 'FAIL'}")

print('\nDone')
