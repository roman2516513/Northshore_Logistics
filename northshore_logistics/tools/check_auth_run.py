import os
import database
import auth

# Ensure we run from project folder
os.chdir(os.path.dirname(__file__) or '.')
PROJECT_ROOT = os.path.abspath(os.path.join(os.getcwd(), '..'))
print('Project root:', PROJECT_ROOT)

# Initialize DB and ensure roles/users
try:
    database.initialise_database()
    print('DB initialised')
except Exception as e:
    print('DB init error', e)

try:
    auth.ensure_default_users()
    print('ensure_default_users ran')
except Exception as e:
    print('ensure_default_users error', e)

conn = database.get_connection()
cur = conn.execute('SELECT id, username, display_name, role_id FROM users')
rows = cur.fetchall()
print('USERS COUNT:', len(rows))
for r in rows:
    print(dict(r))
conn.close()
