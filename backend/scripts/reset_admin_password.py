"""Run once from Render shell to reset the admin password to a new value.

Usage:
    python scripts/reset_admin_password.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
import bcrypt
import libsql

database_url = os.environ['TURSO_DATABASE_URL']
auth_token   = os.environ['TURSO_AUTH_TOKEN']
conn = libsql.connect(database=database_url, auth_token=auth_token)

NEW_HASH = "$2b$12$09XXgZPhnRSX0zE9Uf1PlOvCoc3sjwAc0bBMT4G/b344faqFNMJAq"

conn.execute("DELETE FROM admin_users")
conn.execute("INSERT INTO admin_users (password_hash) VALUES (?)", (NEW_HASH,))
conn.commit()
print("Admin password updated to 'GlobalPerks'.")
