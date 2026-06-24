import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
import bcrypt
import libsql

database_url = os.environ['TURSO_DATABASE_URL']
auth_token = os.environ['TURSO_AUTH_TOKEN']
conn = libsql.connect(database=database_url, auth_token=auth_token)

result = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()
if result[0] > 0:
    print("Admin user already exists.")
    print("To reset: run DELETE FROM admin_users in your Turso dashboard, then re-run this script.")
    sys.exit(1)

password = input("Enter admin password: ").strip()
if len(password) < 8:
    print("Password must be at least 8 characters.")
    sys.exit(1)

password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
conn.execute("INSERT INTO admin_users (password_hash) VALUES (?)", (password_hash,))
conn.commit()
print("Admin user created successfully.")
print("You can now log in at /admin-panel/login/")
