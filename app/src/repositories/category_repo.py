import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.infrastructure.database import get_raw_connection, transaction

class CategoryRepository:
    @staticmethod
    def list_all(only_active: bool = True) -> List[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM categories"
            params = []
            if only_active:
                query += " WHERE is_active = 1"
            query += " ORDER BY display_order ASC, id ASC;"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(cat_id: int) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE id = ?;", (cat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE slug = ?;", (slug.strip().lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def create(name: str, slug: str, description: Optional[str] = None, display_order: int = 0) -> Dict[str, Any]:
        conn = get_raw_connection()
        now_iso = datetime.now().isoformat()
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO categories (name, slug, description, display_order, is_active, created_at)
                    VALUES (?, ?, ?, ?, 1, ?);
                    """,
                    (name.strip(), slug.strip().lower(), description, display_order, now_iso)
                )
                cat_id = cursor.lastrowid
                cursor.execute("SELECT * FROM categories WHERE id = ?;", (cat_id,))
                return dict(cursor.fetchone())
        finally:
            conn.close()

    @staticmethod
    def update(cat_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        if not updates:
            return CategoryRepository.get_by_id(cat_id)
        fields = []
        values = []
        for k, v in updates.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(cat_id)
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                cursor.execute(f"UPDATE categories SET {', '.join(fields)} WHERE id = ?;", values)
                cursor.execute("SELECT * FROM categories WHERE id = ?;", (cat_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def delete(cat_id: int) -> bool:
        conn = get_raw_connection()
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM products WHERE category_id = ?;", (cat_id,))
                if cursor.fetchone()[0] > 0:
                    # Si tiene productos asociados, se desactiva (soft-delete)
                    cursor.execute("UPDATE categories SET is_active = 0 WHERE id = ?;", (cat_id,))
                else:
                    cursor.execute("DELETE FROM categories WHERE id = ?;", (cat_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()
