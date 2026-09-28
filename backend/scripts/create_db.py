"""Create lex_dss database if not exists."""
import psycopg2

conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="postgres", dbname="postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname='lex_dss'")
exists = cur.fetchone()
if not exists:
    cur.execute("CREATE DATABASE lex_dss")
    print("Database lex_dss created")
else:
    print("Database lex_dss already exists")
cur.close()
conn.close()