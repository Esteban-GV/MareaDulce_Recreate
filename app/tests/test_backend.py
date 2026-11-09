import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Configurar base de datos temporal para pruebas aisladas
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_db.close()
os.environ["DATABASE_PATH"] = temp_db.name
os.environ["ADMIN_EMAIL"] = "admin_test@mareadulce.com"
os.environ["ADMIN_PASSWORD"] = "TestAdminPass123!"

from src.main import app
from src.core.config import settings
from src.infrastructure.migrations import run_migrations, backup_database, verify_db_integrity
from src.infrastructure.database import get_raw_connection
from src.infrastructure.seed import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Inicializa la base de datos de prueba con esquema y catálogo semilla."""
    run_migrations()
    seed_database()
    yield
    # Limpieza
    if os.path.exists(temp_db.name):
        try:
            os.remove(temp_db.name)
        except Exception:
            pass

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_and_probes(client):
    """Comprueba sondas de Kubernetes /healthz y /ready."""
    r_health = client.get("/healthz")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    r_ready = client.get("/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "ready"

    r_version = client.get("/api/v1/version")
    assert r_version.status_code == 200
    assert r_version.json()["deployment_strategy"] == "Recreate"

def test_metrics_endpoint(client):
    """Comprueba que /metrics exponga métricas en formato Prometheus."""
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text

def test_catalog_seeded_data(client):
    """Verifica que las 6 categorías y los 12 productos oficiales estén sembrados."""
    # Categorías
    r_cats = client.get("/api/v1/categories")
    assert r_cats.status_code == 200
    cats = r_cats.json()
    assert len(cats) >= 6
    cat_slugs = {c["slug"] for c in cats}
    assert "tortas" in cat_slugs
    assert "cupcakes" in cat_slugs
    assert "galletas" in cat_slugs

    # Productos
    r_prods = client.get("/api/v1/products")
    assert r_prods.status_code == 200
    prods = r_prods.json()
    assert len(prods) == 12

    # Comprobación de precios enteros en COP de la Sección 1.6
    prod_map = {p["name"]: p for p in prods}
    assert prod_map["Torta de vainilla y frutos rojos"]["price_cop"] == 98000
    assert prod_map["Torta tres leches artesanal"]["price_cop"] == 85000
    assert prod_map["Cupcake red velvet individual"]["price_cop"] == 7500
    assert prod_map["Tartaleta de limón merengada"]["stock"] == 0  # Agotado de ejemplo

def test_auth_and_roles(client):
    """Prueba registro, inicio de sesión, JWT y control de acceso basado en roles."""
    # Registro de nuevo cliente
    user_email = "cliente_test@ejemplo.com"
    r_reg = client.post("/api/v1/auth/register", json={
        "email": user_email,
        "full_name": "Cliente de Prueba",
        "password": "Password123!",
        "phone": "+57 311 000 1122"
    })
    assert r_reg.status_code == 201
    client_token = r_reg.json()["access_token"]
    assert client_token is not None

    # Consulta de perfil autenticado /me
    r_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {client_token}"})
    assert r_me.status_code == 200
    assert r_me.json()["email"] == user_email
    assert r_me.json()["role"] == "cliente"

    # Intento de acceso a ruta de admin por parte del cliente -> 403 Forbidden
    r_forbidden = client.get("/api/v1/admin/kpis", headers={"Authorization": f"Bearer {client_token}"})
    assert r_forbidden.status_code == 403

    # Login de Administrador
    r_admin_login = client.post("/api/v1/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    assert r_admin_login.status_code == 200
    admin_token = r_admin_login.json()["access_token"]
    assert r_admin_login.json()["user"]["role"] == "administrador"

    # Acceso exitoso a ruta de admin
    r_kpis = client.get("/api/v1/admin/kpis", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_kpis.status_code == 200
    assert "today_sales_cop" in r_kpis.json()

def test_order_creation_stock_deduction_and_idempotency(client):
    """
    Prueba creación de pedido, cálculo estricto en enteros COP, deducción atómica
    de inventario y resistencia ante duplicados mediante Idempotency-Key.
    """
    # 1. Obtener producto con stock conocido (Caja de 6 cupcakes)
    r_prod = client.get("/api/v1/products/caja-6-cupcakes-surtidos")
    prod = r_prod.json()
    initial_stock = prod["stock"]
    unit_price = prod["price_cop"]
    assert initial_stock >= 5

    order_payload = {
        "customer_name": "María Alejandra Gómez",
        "customer_email": "maria@ejemplo.com",
        "customer_phone": "+57 310 999 8877",
        "delivery_type": "domicilio",
        "delivery_address": "Carrera 15 # 85-30, Apto 402",
        "delivery_date": "2026-11-15",
        "delivery_slot": "Tarde (14:00 - 18:00)",
        "items": [
            {
                "product_id": prod["id"],
                "quantity": 2,
                "customization": {
                    "custom_message": "¡Feliz Cumpleaños Mamá!",
                    "notes": "Por favor colocar lazo de cinta menta"
                }
            }
        ],
        "notes": "Tocar el timbre 402"
    }

    test_idempotency_key = "uuid-test-order-key-12345"

    # 2. Primer envío: creación exitosa
    r_order = client.post(
        "/api/v1/orders",
        json=order_payload,
        headers={"Idempotency-Key": test_idempotency_key}
    )
    assert r_order.status_code == 201
    order_data = r_order.json()
    order_id = order_data["id"]
    order_number = order_data["order_number"]
    assert order_number.startswith("MD-2026-")
    assert order_data["total_cop"] == unit_price * 2
    assert order_data["items"][0]["custom_message"] == "¡Feliz Cumpleaños Mamá!"

    # Verificar que el stock se descontó exactamente en 2 unidades
    r_prod_after = client.get(f"/api/v1/products/{prod['id']}")
    assert r_prod_after.json()["stock"] == initial_stock - 2

    # 3. Segundo envío con la misma Idempotency-Key (simula reintento de red)
    r_order_duplicate = client.post(
        "/api/v1/orders",
        json=order_payload,
        headers={"Idempotency-Key": test_idempotency_key}
    )
    assert r_order_duplicate.status_code == 201
    duplicate_data = r_order_duplicate.json()
    assert duplicate_data["id"] == order_id
    assert duplicate_data["order_number"] == order_number

    # Verificar que el inventario NO se volvió a descontar
    r_prod_after_dup = client.get(f"/api/v1/products/{prod['id']}")
    assert r_prod_after_dup.json()["stock"] == initial_stock - 2

    # 4. Consulta pública de seguimiento por número de orden
    r_track = client.get(f"/api/v1/orders/{order_number}")
    assert r_track.status_code == 200
    assert r_track.json()["customer_name"] == "María Alejandra Gómez"

def test_order_status_transitions_and_cancellation(client):
    """Verifica la máquina de estados de órdenes y reincorporación de stock al cancelar."""
    # Login Admin
    r_login = client.post("/api/v1/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    admin_token = r_login.json()["access_token"]

    # Crear una orden rápida
    r_prod = client.get("/api/v1/products/brownie-arequipe-artesanal")
    prod = r_prod.json()
    stock_before = prod["stock"]

    r_order = client.post("/api/v1/orders", json={
        "customer_name": "Andrés Morales",
        "customer_email": "andres@ejemplo.com",
        "customer_phone": "+57 320 111 2233",
        "delivery_type": "recogida_tienda",
        "delivery_date": "2026-11-20",
        "items": [{"product_id": prod["id"], "quantity": 1}]
    })
    order = r_order.json()
    order_id = order["id"]

    # 1. Transición válida: PENDIENTE -> CONFIRMADO
    r_trans1 = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "CONFIRMADO"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r_trans1.status_code == 200
    assert r_trans1.json()["status"] == "CONFIRMADO"

    # 2. Transición inválida: CONFIRMADO -> ENTREGADO (no permitida sin pasar por PREPARACIÓN y LISTO)
    r_invalid = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "ENTREGADO"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r_invalid.status_code == 400
    assert "Transición inválida" in r_invalid.json()["detail"]

    # 3. Transición a CANCELADO -> debe reincorporar el stock
    r_cancel = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"new_status": "CANCELADO"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r_cancel.status_code == 200
    assert r_cancel.json()["status"] == "CANCELADO"

    # Verificar stock reincorporado
    r_prod_restored = client.get(f"/api/v1/products/{prod['id']}")
    assert r_prod_restored.json()["stock"] == stock_before

def test_insufficient_stock_error(client):
    """Verifica que solicitar más unidades de las disponibles retorne 400 Bad Request."""
    r_prod = client.get("/api/v1/products/tartaleta-limon-merengada")
    prod = r_prod.json()
    assert prod["stock"] == 0

    r_fail = client.post("/api/v1/orders", json={
        "customer_name": "Cliente Sin Stock",
        "customer_email": "nostock@ejemplo.com",
        "customer_phone": "+57 300 000 0000",
        "delivery_type": "recogida_tienda",
        "delivery_date": "2026-11-12",
        "items": [{"product_id": prod["id"], "quantity": 1}]
    })
    assert r_fail.status_code == 400
    assert "Stock insuficiente" in r_fail.json()["detail"]

def test_database_backup_and_integrity():
    """Comprueba la integridad física y la capacidad de respaldo nativo de SQLite."""
    conn = get_raw_connection()
    assert verify_db_integrity(conn) is True
    conn.close()

    backup_file = backup_database(backup_dir="/tmp/marea_test_backups")
    assert os.path.exists(backup_file)
    assert os.path.getsize(backup_file) > 0
    os.remove(backup_file)
