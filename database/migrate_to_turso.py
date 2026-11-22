
import sqlite3
import os
import libsql

from dotenv import load_dotenv
from pathlib import Path

# ==========================================
# 1. LOAD ENVIRONMENT
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

LOCAL_DB_PATH = BASE_DIR / "database" / "medical_images.db"

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")


# ==========================================
# 2. CHECK PATH AND CREDENTIALS
# ==========================================

if not LOCAL_DB_PATH.exists():
    raise FileNotFoundError(
        f"Local database not found: {LOCAL_DB_PATH}"
    )

if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
    raise RuntimeError("Missing Turso credentials in .env")


# ==========================================
# 3. CONNECT
# ==========================================

local_conn = sqlite3.connect(str(LOCAL_DB_PATH))
local_conn.row_factory = sqlite3.Row

cloud_conn = libsql.connect(
    database=TURSO_DATABASE_URL,
    auth_token=TURSO_AUTH_TOKEN
)


# ==========================================
# 4. MIGRATE TABLE
# ==========================================

def migrate_table(table_name):

    print(f"\nMigrating: {table_name}")

    local_cursor = local_conn.cursor()

    local_cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
    """, (table_name,))

    if not local_cursor.fetchone():
        print(f"Table {table_name} does not exist locally.")
        return

    local_cursor.execute(f"PRAGMA table_info({table_name})")

    local_columns = [
        row["name"]
        for row in local_cursor.fetchall()
    ]

    cloud_cursor = cloud_conn.cursor()

    cloud_cursor.execute(f"PRAGMA table_info({table_name})")

    cloud_columns_info = cloud_cursor.fetchall()

    cloud_columns = [
        row[1]
        for row in cloud_columns_info
    ]

    common_columns = [
        column
        for column in local_columns
        if column in cloud_columns
    ]

    if not common_columns:
        print(f"No matching columns in {table_name}.")
        return

    local_cursor.execute(f"SELECT * FROM {table_name}")

    records = local_cursor.fetchall()

    if not records:
        print(f"No records to migrate in {table_name}.")
        return

    columns_sql = ", ".join(common_columns)
    placeholders = ", ".join(["?"] * len(common_columns))

    insert_sql = f"""
        INSERT OR IGNORE INTO {table_name}
        ({columns_sql})
        VALUES ({placeholders})
    """

    count = 0

    for record in records:

        values = tuple(
            record[column]
            for column in common_columns
        )

        cloud_conn.execute(insert_sql, values)
        count += 1

    cloud_conn.commit()

    print(f"Processed {count} records in {table_name}.")


# ==========================================
# 5. MIGRATE IN ORDER
# ==========================================

try:

    migrate_table("users")
    migrate_table("images")
    migrate_table("predictions")

    print("\nMigration completed successfully!")

finally:

    local_conn.close()
    cloud_conn.close()
