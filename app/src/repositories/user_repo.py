import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from src.infrastructure.database import get_raw_connection, transaction
from src.core.security import hash_password

class UserRepository:
    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?;", (email.lower().strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def create_user(email: str, full_name: str, password: str, phone: Optional[str] = None, role: str = "cliente") -> Dict[str, Any]:
        conn = get_raw_connection()
        now_iso = datetime.now().isoformat()
        hashed = hash_password(password)
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (email, full_name, phone, hashed_password, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (email.lower().strip(), full_name.strip(), phone, hashed, role, now_iso, now_iso)
                )
                user_id = cursor.lastrowid
                cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
                return dict(cursor.fetchone())
        finally:
            conn.close()
