import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database file path
DATABASE_PATH = BASE_DIR / "database" / "medical_images.db"

# Upload directory
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"

# Create upload directory if it does not exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


# Connect to SQLite database
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# Initialize database tables
def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Uploaded images table
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

    # Prediction results table
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
    connection.close()

    print("Database initialized successfully!")


# Register a new user
def register_user(full_name, email, password):
    connection = get_connection()

    password_hash = generate_password_hash(password)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash)
            VALUES (?, ?, ?)
        """,
            (full_name, email.lower().strip(), password_hash),
        )

        connection.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:
        return None

    finally:
        connection.close()


# Verify user login
def verify_user(email, password):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, full_name, email, password_hash
            FROM users
            WHERE email = ?
        """,
            (email.lower().strip(),),
        )

        user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            return {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
            }

        return None

    finally:
        connection.close()


# Save uploaded image information
def save_image(user_id, filename, image_category):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO images (user_id, filename, image_category)
            VALUES (?, ?, ?)
        """,
            (user_id, filename, image_category),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# Save prediction result
def save_prediction(image_id, predicted_class, confidence_score, status="completed"):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO predictions (
                image_id,
                predicted_class,
                confidence_score,
                status
            )
            VALUES (?, ?, ?, ?)
        """,
            (image_id, predicted_class, confidence_score, status),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# Retrieve prediction history
def get_prediction_history(user_id=None):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        if user_id is not None:
            cursor.execute(
                """
                SELECT
                    predictions.id AS prediction_id,
                    images.filename,
                    images.image_category,
                    predictions.predicted_class,
                    predictions.confidence_score,
                    predictions.status,
                    predictions.created_at
                FROM predictions
                JOIN images ON predictions.image_id = images.id
                WHERE images.user_id = ?
                ORDER BY predictions.created_at DESC
            """,
                (user_id,),
            )
        else:
            cursor.execute("""
                SELECT
                    predictions.id AS prediction_id,
                    images.filename,
                    images.image_category,
                    predictions.predicted_class,
                    predictions.confidence_score,
                    predictions.status,
                    predictions.created_at
                FROM predictions
                JOIN images ON predictions.image_id = images.id
                ORDER BY predictions.created_at DESC
            """)

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# Delete an uploaded image record
def delete_image(image_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM images
            WHERE id = ?
        """,
            (image_id,),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# Run this file directly to initialize database
if __name__ == "__main__":
    initialize_database()
