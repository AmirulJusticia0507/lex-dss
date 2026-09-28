"""Verify superadmin credentials in database."""
import psycopg2
import bcrypt

conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="postgres", dbname="lex_dss")
cur = conn.cursor()
cur.execute(
    "SELECT id, email, role, is_superuser, is_active, hashed_password "
    "FROM users WHERE email='superadmin@lex.local'"
)
row = cur.fetchone()
if row:
    print("ID:", row[0])
    print("Email:", row[1])
    print("Role:", row[2])
    print("is_superuser:", row[3])
    print("is_active:", row[4])
    print("Password hash:", row[5][:20] + "...")
    ok = bcrypt.checkpw("gedangbosok".encode(), row[5].encode())
    print("Password match:", ok)
else:
    print("NOT FOUND")
cur.close()
conn.close()