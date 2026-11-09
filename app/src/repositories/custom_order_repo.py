import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.infrastructure.database import get_raw_connection, transaction

class CustomOrderRepository:
    @staticmethod
    def create(data: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_raw_connection()
        now_iso = datetime.now().isoformat()
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO custom_order_requests (
                        customer_name, customer_email, customer_phone, product_type,
                        servings, required_date, description, reference_image_url,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?);
                    """,
                    (
                        data["customer_name"].strip(), data["customer_email"].strip().lower(),
                        data["customer_phone"].strip(), data["product_type"].strip(),
                        int(data["servings"]), data["required_date"], data["description"].strip(),
                        data.get("reference_image_url"), now_iso
                    )
                )
                req_id = cursor.lastrowid
                cursor.execute("SELECT * FROM custom_order_requests WHERE id = ?;", (req_id,))
                return dict(cursor.fetchone())
        finally:
            conn.close()

    @staticmethod
    def list_all(limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM custom_order_requests ORDER BY id DESC LIMIT ?;", (limit,))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def update_status(req_id: int, status: str, estimated_price_cop: Optional[int] = None) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                if estimated_price_cop is not None:
                    cursor.execute(
                        "UPDATE custom_order_requests SET status = ?, estimated_price_cop = ? WHERE id = ?;",
                        (status, int(estimated_price_cop), req_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE custom_order_requests SET status = ? WHERE id = ?;",
                        (status, req_id)
                    )
                cursor.execute("SELECT * FROM custom_order_requests WHERE id = ?;", (req_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()
