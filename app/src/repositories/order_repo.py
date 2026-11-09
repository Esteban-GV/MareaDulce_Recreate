import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.domain.constants import OrderStatus, VALID_ORDER_TRANSITIONS
from src.infrastructure.database import get_raw_connection, transaction

class OrderRepository:
    @classmethod
    def _fetch_order_with_items(cls, cursor: sqlite3.Cursor, order_id: int) -> Optional[Dict[str, Any]]:
        cursor.execute("SELECT * FROM orders WHERE id = ?;", (order_id,))
        order_row = cursor.fetchone()
        if not order_row:
            return None
        order = dict(order_row)
        
        cursor.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC;", (order_id,))
        items = [dict(r) for r in cursor.fetchall()]
        order["items"] = items
        return order

    @classmethod
    def get_by_id(cls, order_id: int) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            return cls._fetch_order_with_items(cursor, order_id)
        finally:
            conn.close()

    @classmethod
    def get_by_order_number(cls, order_number: str) -> Optional[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM orders WHERE order_number = ?;", (order_number.strip().upper(),))
            row = cursor.fetchone()
            if not row:
                return None
            return cls._fetch_order_with_items(cursor, row[0])
        finally:
            conn.close()

    @classmethod
    def get_by_idempotency_key(cls, key: str) -> Optional[Dict[str, Any]]:
        if not key:
            return None
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM orders WHERE idempotency_key = ?;", (key.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return cls._fetch_order_with_items(cursor, row[0])
        finally:
            conn.close()

    @classmethod
    def create_order(
        cls,
        order_data: Dict[str, Any],
        items_data: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Crea un pedido con control atómico de concurrencia e inventario (BEGIN IMMEDIATE)
        e idempotencia estricta.
        """
        # 1. Verificación previa de idempotencia
        if idempotency_key:
            existing = cls.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        conn = get_raw_connection()
        now = datetime.now()
        now_iso = now.isoformat()
        year = now.year

        try:
            # Transacción exclusiva para evitar condiciones de carrera en inventario
            with transaction(conn, immediate=True):
                cursor = conn.cursor()

                # Re-verificar idempotencia dentro de la transacción por concurrencia
                if idempotency_key:
                    cursor.execute("SELECT id FROM orders WHERE idempotency_key = ?;", (idempotency_key,))
                    row = cursor.fetchone()
                    if row:
                        return cls._fetch_order_with_items(cursor, row[0])

                # 2. Validar productos, disponibilidad y calcular total en enteros COP
                total_cop = 0
                prepared_items = []

                for item in items_data:
                    prod_id = item["product_id"]
                    qty = int(item["quantity"])
                    if qty <= 0:
                        raise ValueError("La cantidad debe ser mayor a cero.")

                    cursor.execute(
                        "SELECT id, name, price_cop, stock, is_active FROM products WHERE id = ?;",
                        (prod_id,)
                    )
                    prod = cursor.fetchone()
                    if not prod:
                        raise ValueError(f"El producto con ID {prod_id} no existe en el catálogo.")
                    if not prod["is_active"]:
                        raise ValueError(f"El producto '{prod['name']}' no está disponible actualmente.")
                    if prod["stock"] < qty:
                        raise ValueError(
                            f"Stock insuficiente para '{prod['name']}'. Disponible: {prod['stock']}, solicitado: {qty}."
                        )

                    # Descuento atómico de inventario
                    cursor.execute(
                        "UPDATE products SET stock = stock - ?, updated_at = ? WHERE id = ?;",
                        (qty, now_iso, prod_id)
                    )

                    unit_price = int(prod["price_cop"])
                    subtotal = unit_price * qty
                    total_cop += subtotal

                    custom = item.get("customization") or {}
                    msg = custom.get("custom_message")
                    if msg and len(msg) > 40:
                        msg = msg[:40]

                    prepared_items.append({
                        "product_id": prod_id,
                        "product_name": prod["name"],
                        "unit_price_cop": unit_price,
                        "quantity": qty,
                        "subtotal_cop": subtotal,
                        "servings": custom.get("servings"),
                        "flavor": custom.get("flavor"),
                        "custom_message": msg,
                        "delivery_slot": custom.get("delivery_slot"),
                        "notes": custom.get("notes")
                    })

                # 3. Generar número de orden con formato legible MD-AAAA-NNNNNN
                cursor.execute("SELECT count(*) FROM orders WHERE order_number LIKE ?;", (f"MD-{year}-%",))
                order_seq = cursor.fetchone()[0] + 1
                order_number = f"MD-{year}-{order_seq:06d}"

                # 4. Insertar orden principal
                cursor.execute(
                    """
                    INSERT INTO orders (
                        order_number, user_id, customer_name, customer_email, customer_phone,
                        delivery_type, delivery_address, delivery_date, delivery_slot,
                        status, payment_method, payment_status, total_cop, notes,
                        idempotency_key, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?, 'PAGADO_DEMO', ?, ?, ?, ?, ?);
                    """,
                    (
                        order_number, user_id, order_data["customer_name"].strip(),
                        order_data["customer_email"].strip().lower(), order_data["customer_phone"].strip(),
                        order_data["delivery_type"], order_data.get("delivery_address"),
                        order_data["delivery_date"], order_data.get("delivery_slot"),
                        order_data.get("payment_method", "simulado_demo"), total_cop,
                        order_data.get("notes"), idempotency_key, now_iso, now_iso
                    )
                )
                order_id = cursor.lastrowid

                # 5. Insertar ítems del pedido
                for pi in prepared_items:
                    cursor.execute(
                        """
                        INSERT INTO order_items (
                            order_id, product_id, product_name, unit_price_cop, quantity,
                            subtotal_cop, servings, flavor, custom_message, delivery_slot, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            order_id, pi["product_id"], pi["product_name"], pi["unit_price_cop"],
                            pi["quantity"], pi["subtotal_cop"], pi["servings"], pi["flavor"],
                            pi["custom_message"], pi["delivery_slot"], pi["notes"]
                        )
                    )

                return cls._fetch_order_with_items(cursor, order_id)
        finally:
            conn.close()

    @classmethod
    def update_status(cls, order_id: int, new_status: OrderStatus) -> Dict[str, Any]:
        """Aplica una transición de estado validando las reglas de negocio."""
        conn = get_raw_connection()
        now_iso = datetime.now().isoformat()
        try:
            with transaction(conn, immediate=True):
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM orders WHERE id = ?;", (order_id,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Orden ID {order_id} no encontrada.")
                
                current_status = OrderStatus(row[0])
                if new_status == current_status:
                    return cls._fetch_order_with_items(cursor, order_id)

                allowed = VALID_ORDER_TRANSITIONS.get(current_status, set())
                if new_status not in allowed:
                    raise ValueError(
                        f"Transición inválida: no se permite cambiar de '{current_status.value}' a '{new_status.value}'."
                    )

                # Si se cancela la orden, se reintegra el stock a inventario
                if new_status == OrderStatus.CANCELADO:
                    cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?;", (order_id,))
                    items = cursor.fetchall()
                    for item in items:
                        cursor.execute(
                            "UPDATE products SET stock = stock + ?, updated_at = ? WHERE id = ?;",
                            (item["quantity"], now_iso, item["product_id"])
                        )

                cursor.execute(
                    "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?;",
                    (new_status.value, now_iso, order_id)
                )
                return cls._fetch_order_with_items(cursor, order_id)
        finally:
            conn.close()

    @classmethod
    def list_orders(
        cls,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        conn = get_raw_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT id FROM orders WHERE 1=1"
            params = []
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            if status:
                query += " AND status = ?"
                params.append(status.upper())
            query += " ORDER BY id DESC LIMIT ? OFFSET ?;"
            params.extend([limit, offset])

            cursor.execute(query, params)
            order_ids = [r[0] for r in cursor.fetchall()]
            results = []
            for oid in order_ids:
                o = cls._fetch_order_with_items(cursor, oid)
                if o:
                    results.append(o)
            return results
        finally:
            conn.close()
