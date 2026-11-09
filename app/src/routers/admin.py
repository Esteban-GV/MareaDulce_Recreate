from datetime import datetime
from fastapi import APIRouter, Depends
from src.domain.schemas import KpiSummaryOut
from src.core.security import require_admin
from src.infrastructure.database import get_raw_connection

router = APIRouter(prefix="/api/v1/admin", tags=["Administración"])

@router.get("/kpis", response_model=KpiSummaryOut, summary="Métricas y KPIs del Dashboard Administrativo")
def get_kpis(_=Depends(require_admin)):
    """Retorna los indicadores clave de negocio para el panel del administrador."""
    conn = get_raw_connection()
    today_str = datetime.now().strftime("%Y-%m-%d")
    month_str = datetime.now().strftime("%Y-%m")

    try:
        cursor = conn.cursor()

        # 1. Ventas del día (órdenes no canceladas)
        cursor.execute(
            """
            SELECT coalesce(sum(total_cop), 0) FROM orders
            WHERE created_at LIKE ? AND status != 'CANCELADO';
            """,
            (f"{today_str}%",)
        )
        today_sales = cursor.fetchone()[0]

        # 2. Pedidos pendientes
        cursor.execute("SELECT count(*) FROM orders WHERE status = 'PENDIENTE';")
        pending_orders = cursor.fetchone()[0]

        # 3. Pedidos del mes
        cursor.execute("SELECT count(*) FROM orders WHERE created_at LIKE ?;", (f"{month_str}%",))
        month_orders = cursor.fetchone()[0]

        # 4. Productos con bajo stock (<= 5 unidades)
        cursor.execute("SELECT count(*) FROM products WHERE stock <= 5 AND is_active = 1;")
        low_stock = cursor.fetchone()[0]

        # 5. Total productos activos
        cursor.execute("SELECT count(*) FROM products WHERE is_active = 1;")
        total_products = cursor.fetchone()[0]

        return KpiSummaryOut(
            today_sales_cop=today_sales,
            pending_orders_count=pending_orders,
            month_orders_count=month_orders,
            low_stock_products_count=low_stock,
            total_catalog_products=total_products
        )
    finally:
        conn.close()

@router.get("/inventory", summary="Inventario administrativo consolidado")
def get_inventory(_=Depends(require_admin)):
    """Retorna el listado completo de inventario con alertas de stock."""
    conn = get_raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.id, p.name, c.name as category, p.price_cop, p.stock,
                   p.is_active, p.badge,
                   CASE WHEN p.stock = 0 THEN 'AGOTADO'
                        WHEN p.stock <= 5 THEN 'BAJO_STOCK'
                        ELSE 'DISPONIBLE' END as stock_status
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.stock ASC, p.id ASC;
            """
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()
