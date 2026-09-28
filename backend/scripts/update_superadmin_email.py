"""Update superadmin email to a valid address."""
import psycopg2

conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="postgres", dbname="lex_dss")
cur = conn.cursor()
cur.execute(
    "UPDATE users SET email='superadmin@lexdss.io' WHERE email='superadmin@lex.local'"
)
conn.commit()
print("Updated superadmin email to superadmin@lexdss.io")
cur.close()
conn.close()