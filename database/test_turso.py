import os
import libsql
from dotenv import load_dotenv

load_dotenv()

conn = libsql.connect(
    database=os.getenv("TURSO_DATABASE_URL"),
    auth_token=os.getenv("TURSO_AUTH_TOKEN")
)

conn.execute("""
    CREATE TABLE IF NOT EXISTS connection_test (
        id INTEGER PRIMARY KEY,
        message TEXT
    )
""")

conn.execute(
    "INSERT INTO connection_test (message) VALUES (?)",
    ("Turso connection successful!",)
)

conn.commit()

rows = conn.execute(
    "SELECT * FROM connection_test"
).fetchall()

print(rows)

conn.close()