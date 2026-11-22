
import sqlite3
import os
import libsql

from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# 1. PROJECT PATHS & ENVIRONMENT
# ==========================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_FOLDER = BASE_DIR / "database"
DATABASE_PATH = DATABASE_FOLDER / "medical_images.db"

UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"

DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")


# ==========================================
# 2. ROW COMPATIBILITY
# ==========================================

class HybridRow(dict):
    """Supports row['column'] and row[0] access."""

    def __init__(self, columns, values):
        super().__init__(zip(columns, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


class CursorWrapper:

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, sql, parameters=()):
        self.cursor.execute(sql, parameters)
        return self

    def fetchone(self):
        row = self.cursor.fetchone()

        if row is None:
            return None

        columns = [
            column[0]
            for column in self.cursor.description
        ]

        return HybridRow(columns, row)

    def fetchall(self):
        rows = self.cursor.fetchall()

        if not rows:
            return []

        columns = [
            column[0]
            for column in self.cursor.description
        ]

        return [
            HybridRow(columns, row)
            for row in rows
        ]

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def description(self):
        return self.cursor.description


class ConnectionWrapper:

    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        return CursorWrapper(self.connection.cursor())

    def execute(self, sql, parameters=()):
        cursor = self.connection.execute(sql, parameters)
        return CursorWrapper(cursor)

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


# ==========================================
# 3. DATABASE CONNECTION
# ==========================================

def get_connection():

    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise RuntimeError(
            "TURSO_DATABASE_URL and TURSO_AUTH_TOKEN "
            "must be set in your .env file."
        )

    connection = libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )

    return ConnectionWrapper(connection)


# ==========================================
# 4. INITIALIZE DATABASE
# ==========================================

def initialize_database():

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # USERS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration for users table
        cursor.execute("PRAGMA table_info(users)")

        columns = [
            column["name"]
            for column in cursor.fetchall()
        ]

        if "role" not in columns:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
            """)

        # IMAGES TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT NOT NULL,
                image_category TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
            )
        """)

        # PREDICTIONS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                predicted_class TEXT,
                confidence_score REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (image_id)
                REFERENCES images(id)
                ON DELETE CASCADE
            )
        """)

        connection.commit()

        print("Cloud database initialized successfully!")

    finally:
        connection.close()


# ==========================================
# 5. REGISTER NEW USER
# ==========================================

def register_user(full_name, email, password):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (
                full_name,
                email,
                password_hash,
                role
            )
            VALUES (?, ?, ?, 'user')
        """, (
            full_name.strip(),
            email.lower().strip(),
            password_hash
        ))

        connection.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:
        return None

    finally:
        connection.close()


# ==========================================
# 6. VERIFY USER LOGIN
# ==========================================

def verify_user(email, password):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, full_name, email, password_hash, role
            FROM users
            WHERE email = ?
        """, (email.lower().strip(),))

        user = cursor.fetchone()

        if user and check_password_hash(
            user["password_hash"], password
        ):

            return {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }

        return None

    finally:
        connection.close()


# ==========================================
# 7. GET USER DETAILS
# ==========================================

def get_user_by_id(user_id):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, full_name, email, role, created_at
            FROM users
            WHERE id = ?
        """, (user_id,))

        user = cursor.fetchone()

        return dict(user) if user else None

    finally:
        connection.close()


# ==========================================
# 8. SAVE UPLOADED IMAGE INFORMATION
# ==========================================

def save_image(user_id, filename, image_category):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO images (
                user_id,
                filename,
                image_category
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            filename,
            image_category
        ))

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# ==========================================
# 9. SAVE AI PREDICTION RESULT
# ==========================================

def save_prediction(
    image_id,
    predicted_class,
    confidence_score,
    status="completed"
):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO predictions (
                image_id,
                predicted_class,
                confidence_score,
                status
            )
            VALUES (?, ?, ?, ?)
        """, (
            image_id,
            predicted_class,
            confidence_score,
            status
        ))

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# ==========================================
# 10. GET USER PREDICTION HISTORY
# ==========================================

def get_prediction_history(user_id=None):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if user_id is not None:

            cursor.execute("""
                SELECT
                    predictions.id AS prediction_id,
                    images.id AS image_id,
                    images.filename,
                    images.image_category,
                    predictions.predicted_class,
                    predictions.confidence_score,
                    predictions.status,
                    predictions.created_at

                FROM predictions

                JOIN images
                ON predictions.image_id = images.id

                WHERE images.user_id = ?

                ORDER BY predictions.created_at DESC
            """, (user_id,))

        else:

            cursor.execute("""
                SELECT
                    predictions.id AS prediction_id,
                    images.id AS image_id,
                    images.filename,
                    images.image_category,
                    predictions.predicted_class,
                    predictions.confidence_score,
                    predictions.status,
                    predictions.created_at

                FROM predictions

                JOIN images
                ON predictions.image_id = images.id

                ORDER BY predictions.created_at DESC
            """)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# ==========================================
# 11. GET ALL REGISTERED USERS (ADMIN)
# ==========================================

def get_all_users():

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                full_name,
                email,
                role,
                created_at
            FROM users
            ORDER BY created_at DESC
        """)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# ==========================================
# 12. GET ALL UPLOADED IMAGES (ADMIN)
# ==========================================

def get_all_images():

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                images.id,
                images.user_id,
                users.full_name,
                images.filename,
                images.image_category,
                images.uploaded_at

            FROM images

            LEFT JOIN users
            ON images.user_id = users.id

            ORDER BY images.uploaded_at DESC
        """)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# ==========================================
# 13. GET ALL PREDICTIONS (ADMIN)
# ==========================================

def get_all_predictions():

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                predictions.id AS prediction_id,
                images.filename,
                images.image_category,
                users.full_name,
                predictions.predicted_class,
                predictions.confidence_score,
                predictions.status,
                predictions.created_at

            FROM predictions

            JOIN images
            ON predictions.image_id = images.id

            LEFT JOIN users
            ON images.user_id = users.id

            ORDER BY predictions.created_at DESC
        """)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# ==========================================
# 14. DASHBOARD STATISTICS (ADMIN)
# ==========================================

def get_dashboard_statistics():

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM images")
        total_images = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]

        cursor.execute("""
            SELECT image_category, COUNT(*) AS total
            FROM images
            GROUP BY image_category
        """)

        category_counts = {
            row["image_category"]: row["total"]
            for row in cursor.fetchall()
        }

        return {
            "total_users": total_users,
            "total_images": total_images,
            "total_predictions": total_predictions,
            "category_counts": category_counts
        }

    finally:
        connection.close()


# ==========================================
# 15. DELETE IMAGE RECORD
# ==========================================

def delete_image(image_id, user_id=None):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if user_id is not None:

            cursor.execute("""
                DELETE FROM images
                WHERE id = ? AND user_id = ?
            """, (image_id, user_id))

        else:

            cursor.execute("""
                DELETE FROM images
                WHERE id = ?
            """, (image_id,))

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# ==========================================
# 16. INITIALIZE DATABASE WHEN RUN DIRECTLY
# ==========================================

if __name__ == "__main__":
    initialize_database()
