import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.infrastructure.database import get_raw_connection, transaction

class ProductRepository:
    @staticmethod
    def _parse_product(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        if "allergens" in data and isinstance(data["allergens"], str):
            try:
                data["allergens"] = json.loads(data["allergens"])
            except Exception:
                data["allergens"] = []
        return data

    @classmethod
    def list_products(
        cls,
        category_slug: Optional[str] = None,
        search: Optional[str] = None,
        only_active: bool = True,
        only_in_stock: bool = False,
        featured_only: bool = False
    ) -> List[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT p.*, c.name as category_name
                FROM products p
                JOIN categories c ON p.category_id = c.id
                WHERE 1=1
            """
            params = []
            if only_active:
                query += " AND p.is_active = 1 AND c.is_active = 1"
            if category_slug:
                query += " AND c.slug = ?"
                params.append(category_slug.strip().lower())
            if search:
                query += " AND (p.name LIKE ? OR p.description LIKE ?)"
                term = f"%{search.strip()}%"
                params.extend([term, term])
            if only_in_stock:
                query += " AND p.stock > 0"
            if featured_only:
                query += " AND p.is_featured = 1"
                
            query += " ORDER BY p.is_featured DESC, p.id ASC;"
            cursor.execute(query, params)
            return [cls._parse_product(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, product_id: int) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, c.name as category_name
                FROM products p
                JOIN categories c ON p.category_id = c.id
                WHERE p.id = ?;
                """,
                (product_id,)
            )
            row = cursor.fetchone()
            return cls._parse_product(row) if row else None
        finally:
            conn.close()

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, c.name as category_name
                FROM products p
                JOIN categories c ON p.category_id = c.id
                WHERE p.slug = ?;
                """,
                (slug.strip().lower(),)
            )
            row = cursor.fetchone()
            return cls._parse_product(row) if row else None
        finally:
            conn.close()

    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_raw_connection()
        now_iso = datetime.now().isoformat()
        allergens_json = json.dumps(data.get("allergens", []))
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO products (
                        category_id, name, slug, description, price_cop, servings,
                        prep_time_hours, ingredients, allergens, image_url, badge,
                        stock, is_active, is_featured, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        data["category_id"], data["name"].strip(), data["slug"].strip().lower(),
                        data["description"].strip(), int(data["price_cop"]), data["servings"],
                        data.get("prep_time_hours", 24), data.get("ingredients", ""),
                        allergens_json, data.get("image_url"), data.get("badge"),
                        int(data.get("stock", 0)), 1 if data.get("is_active", True) else 0,
                        1 if data.get("is_featured", False) else 0, now_iso, now_iso
                    )
                )
                prod_id = cursor.lastrowid
                return cls.get_by_id(prod_id)
        finally:
            conn.close()

    @classmethod
    def update(cls, product_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        if not updates:
            return cls.get_by_id(product_id)
        updates["updated_at"] = datetime.now().isoformat()
        if "allergens" in updates and isinstance(updates["allergens"], list):
            updates["allergens"] = json.dumps(updates["allergens"])
        fields = []
        values = []
        for k, v in updates.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(product_id)
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                cursor.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = ?;", values)
                return cls.get_by_id(product_id)
        finally:
            conn.close()

    @classmethod
    def update_stock(cls, product_id: int, new_stock: int) -> Optional[Dict[str, Any]]:
        return cls.update(product_id, {"stock": max(0, new_stock)})
