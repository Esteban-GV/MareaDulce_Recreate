import os
import sqlite3
import logging
from datetime import datetime
from src.core.config import settings
from src.infrastructure.database import get_raw_connection

logger = logging.getLogger("marea.migrations")

SCHEMA_V1_SQL = """
-- Tabla de control de migraciones
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);

-- Tabla de Usuarios y Roles
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'cliente',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Tabla de Categorías de Pastelería
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

-- Tabla de Productos del Catálogo Oficial
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    price_cop INTEGER NOT NULL CHECK (price_cop >= 0),
    servings TEXT NOT NULL,
    prep_time_hours INTEGER NOT NULL DEFAULT 24,
    ingredients TEXT NOT NULL,
    allergens TEXT NOT NULL DEFAULT '[]',
    image_url TEXT,
    badge TEXT,
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    is_active INTEGER NOT NULL DEFAULT 1,
    is_featured INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Tabla de Órdenes / Pedidos con soporte de Idempotencia
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    delivery_type TEXT NOT NULL,
    delivery_address TEXT,
    delivery_date TEXT NOT NULL,
    delivery_slot TEXT,
    status TEXT NOT NULL DEFAULT 'PENDIENTE',
    payment_method TEXT NOT NULL DEFAULT 'simulado_demo',
    payment_status TEXT NOT NULL DEFAULT 'PAGADO_DEMO',
    total_cop INTEGER NOT NULL CHECK (total_cop >= 0),
    notes TEXT,
    idempotency_key TEXT UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Tabla de Ítems del Pedido con Personalizaciones
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_name TEXT NOT NULL,
    unit_price_cop INTEGER NOT NULL CHECK (unit_price_cop >= 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    subtotal_cop INTEGER NOT NULL CHECK (subtotal_cop >= 0),
    servings TEXT,
    flavor TEXT,
    custom_message TEXT,
    delivery_slot TEXT,
    notes TEXT
);

-- Tabla de Solicitudes de Pedidos Personalizados
CREATE TABLE IF NOT EXISTS custom_order_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    product_type TEXT NOT NULL,
    servings INTEGER NOT NULL CHECK (servings > 0),
    required_date TEXT NOT NULL,
    description TEXT NOT NULL,
    reference_image_url TEXT,
    status TEXT NOT NULL DEFAULT 'PENDIENTE',
    estimated_price_cop INTEGER,
    created_at TEXT NOT NULL
);

-- Índices de consulta rápida
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_customer_email ON orders(customer_email);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
"""

def verify_db_integrity(conn: sqlite3.Connection) -> bool:
    """Ejecuta PRAGMA integrity_check y valida que retorne 'ok'."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchone()
    if result and result[0] == "ok":
        return True
    logger.error("Fallo de integridad en base de datos: %s", result)
    return False

def backup_database(backup_dir: str = "/data/backups") -> str:
    """Realiza un respaldo consistente usando la API nativa .backup de SQLite."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"marea_dulce_backup_{timestamp}.db")
    
    source_conn = get_raw_connection()
    try:
        dest_conn = sqlite3.connect(backup_path)
        source_conn.backup(dest_conn)
        dest_conn.close()
        logger.info("Respaldo consistente completado en: %s", backup_path)
        return backup_path
    finally:
        source_conn.close()

def run_migrations():
    """Aplica las migraciones estructurales verificando integridad antes y después."""
    logger.info("Verificando migraciones de base de datos en %s...", settings.DATABASE_PATH)
    conn = get_raw_connection()
    try:
        # 1. Comprobación de integridad inicial si el archivo ya existe
        if os.path.exists(settings.DATABASE_PATH) and os.path.getsize(settings.DATABASE_PATH) > 0:
            if not verify_db_integrity(conn):
                raise RuntimeError("La base de datos existente no superó PRAGMA integrity_check")

        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Verificar versión actual
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations';")
        has_migrations_table = cursor.fetchone()[0] > 0
        
        current_version = 0
        if has_migrations_table:
            cursor.execute("SELECT coalesce(max(version), 0) FROM schema_migrations;")
            current_version = cursor.fetchone()[0]
            
        logger.info("Versión actual del esquema: %d", current_version)
        
        # Aplicar Versión 1 si no está aplicada
        if current_version < 1:
            logger.info("Aplicando Migración v1 (Esquema relacional Marea Dulce)...")
            cursor.executescript(SCHEMA_V1_SQL)
            cursor.execute(
                "INSERT INTO schema_migrations (version, applied_at, description) VALUES (?, ?, ?);",
                (1, datetime.now().isoformat(), "Esquema inicial Marea Dulce E-Commerce")
            )
            logger.info("Migración v1 aplicada con éxito.")
            
        # 2. Comprobación de integridad final
        if not verify_db_integrity(conn):
            raise RuntimeError("Fallo de PRAGMA integrity_check tras aplicar migraciones")
            
        logger.info("Integridad verificada [OK]. Esquema actualizado a la versión más reciente.")
    finally:
        conn.close()
