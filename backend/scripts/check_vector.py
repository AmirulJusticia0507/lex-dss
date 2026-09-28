"""Check if vector extension is available and install if needed."""
import psycopg2

conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="postgres", dbname="lex_dss")
cur = conn.cursor()
cur.execute("SELECT * FROM pg_available_extensions WHERE name='vector'")
rows = cur.fetchall()
print("Vector available:", rows)
cur.close()
conn.close()