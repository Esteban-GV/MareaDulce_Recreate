import os
import time
import socket
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# ==============================================================================
# Variables de Configuración y Entorno
# ==============================================================================
APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")
APP_ENV = os.getenv("APP_ENV", "production")
IS_V1 = APP_VERSION.startswith("v1")
SCHEMA_VERSION = "schema_v1_legacy" if IS_V1 else "schema_v2_migrated"
APP_COLOR = os.getenv("APP_COLOR", "#1e3a8a" if IS_V1 else "#14532d")
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DB_PATH = DATA_DIR / "recreate_platform.db"
POD_NAME = os.getenv("POD_NAME", socket.gethostname())
POD_IP = os.getenv("POD_IP", "127.0.0.1")
NODE_NAME = os.getenv("NODE_NAME", "minikube")

# ==============================================================================
# Métricas de Telemetría Prometheus (Modelo RED, Dominio y Almacenamiento)
# ==============================================================================
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total acumulado de peticiones HTTP atendidas por la aplicacion",
    ["method", "endpoint", "status_code", "version"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Distribucion de latencia en peticiones HTTP",
    ["method", "endpoint", "version"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

APP_INFO_GAUGE = Gauge(
    "app_version_info",
    "Informacion de version, esquema y metadatos de la carga de trabajo",
    ["version", "schema_version", "environment", "pod_name", "node_name"],
)
APP_INFO_GAUGE.labels(
    version=APP_VERSION,
    schema_version=SCHEMA_VERSION,
    environment=APP_ENV,
    pod_name=POD_NAME,
    node_name=NODE_NAME,
).set(1)

PVC_OPERATIONS_TOTAL = Counter(
    "app_pvc_storage_operations_total",
    "Total de operaciones de lectura y escritura sobre el volumen PVC",
    ["operation", "status"],
)

DOMAIN_TRANSACTIONS_TOTAL = Counter(
    "app_ledger_transactions_total",
    "Total de transacciones contables registradas en la base de datos del PVC",
    ["schema_version", "version", "status"],
)

AUTH_EVENTS_TOTAL = Counter(
    "app_auth_events_total",
    "Total de eventos de autenticacion SSO/OIDC y MFA",
    ["operation", "result"],
)

START_TIME = time.time()


# ==============================================================================
# Modelos de Datos (Pydantic)
# ==============================================================================
class TransactionInput(BaseModel):
    concept: str = "Liquidacion de orden corporativa"
    amount_usd: float = 250.00
    currency: Optional[str] = "USD"


class AuthTokenRequest(BaseModel):
    username: str = "esteban.guarin@universidad.edu.co"
    mfa_code: str = "482910"


# ==============================================================================
# Inicialización de Base de Datos SQLite en PVC y Migración de Esquema
# ==============================================================================
def init_and_migrate_db() -> Dict[str, Any]:
    """
    Inicializa la base de datos transaccional en el PVC (/data/recreate_platform.db).
    En v1.0.0 opera con 'schema_v1_legacy'.
    En v2.0.0 ejecuta una migración estructural destructiva/exclusiva a 'schema_v2_migrated',
    demostrando por qué v1 y v2 no pueden coexistir simultáneamente.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=15.0, isolation_level=None)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout = 15000")
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by_pod TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_code TEXT NOT NULL,
                concept TEXT NOT NULL,
                amount_usd REAL NOT NULL,
                app_version TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                pod_origin TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # Verificar columnas existentes en ledger_transactions
        cursor.execute("PRAGMA table_info(ledger_transactions)")
        columns = [row[1] for row in cursor.fetchall()]

        now_iso = datetime.now(timezone.utc).isoformat()

        if not IS_V1:
            # Migración exclusiva de v2.0.0: añade columnas de auditoría fiscal e integridad
            if "audit_hash" not in columns:
                cursor.execute(
                    "ALTER TABLE ledger_transactions ADD COLUMN currency TEXT DEFAULT 'USD'"
                )
                cursor.execute(
                    "ALTER TABLE ledger_transactions ADD COLUMN tax_rate REAL DEFAULT 0.19"
                )
                cursor.execute(
                    "ALTER TABLE ledger_transactions ADD COLUMN audit_hash TEXT DEFAULT 'MIGRATED_FROM_V1'"
                )

        cursor.execute(
            """
            INSERT INTO schema_metadata (key, value, updated_at, updated_by_pod)
            VALUES ('active_schema', ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at,
                updated_by_pod = excluded.updated_by_pod
            """,
            (SCHEMA_VERSION, now_iso, POD_NAME),
        )

        # Semilla inicial si la tabla está vacía
        cursor.execute("SELECT COUNT(*) FROM ledger_transactions")
        count = cursor.fetchone()[0]
        if count == 0:
            tx_seed = f"TX-INIT-{int(time.time())}"
            if IS_V1 or "audit_hash" not in columns and IS_V1:
                cursor.execute(
                    """
                    INSERT INTO ledger_transactions
                    (tx_code, concept, amount_usd, app_version, schema_version, pod_origin, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx_seed,
                        " Apertura de libro contable en volumen persistente PVC",
                        1000.00,
                        APP_VERSION,
                        SCHEMA_VERSION,
                        POD_NAME,
                        now_iso,
                    ),
                )
            else:
                digest = hashlib.sha256(f"{tx_seed}:{APP_VERSION}".encode()).hexdigest()[:16]
                cursor.execute(
                    """
                    INSERT INTO ledger_transactions
                    (tx_code, concept, amount_usd, app_version, schema_version, pod_origin, created_at, currency, tax_rate, audit_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx_seed,
                        "Apertura de libro contable en volumen persistente PVC (Esquema V2)",
                        1000.00,
                        APP_VERSION,
                        SCHEMA_VERSION,
                        POD_NAME,
                        now_iso,
                        "USD",
                        0.19,
                        digest,
                    ),
                )

        cursor.execute("COMMIT")
        conn.close()
        PVC_OPERATIONS_TOTAL.labels(operation="schema_init", status="success").inc()
        DOMAIN_TRANSACTIONS_TOTAL.labels(
            schema_version=SCHEMA_VERSION, version=APP_VERSION, status="committed"
        ).inc(0)
        return {"status": "ok", "schema_version": SCHEMA_VERSION}
    except Exception as exc:
        try:
            conn.execute("ROLLBACK")
            conn.close()
        except Exception:
            pass
        PVC_OPERATIONS_TOTAL.labels(operation="schema_init", status="error").inc()
        return {"status": "error", "detail": str(exc)}


def get_and_increment_counter() -> int:
    """Gestiona un contador atómico en el volumen persistente (PVC)."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        counter_file = DATA_DIR / "counter.txt"
        current_val = 0
        if counter_file.exists():
            content = counter_file.read_text().strip()
            current_val = int(content) if content.isdigit() else 0

        current_val += 1
        counter_file.write_text(str(current_val))
        PVC_OPERATIONS_TOTAL.labels(operation="write", status="success").inc()
        return current_val
    except Exception:
        PVC_OPERATIONS_TOTAL.labels(operation="write", status="error").inc()
        return -1


def record_transaction(concept: str, amount_usd: float, currency: str = "USD") -> Dict[str, Any]:
    """Inserta una transacción contable en SQLite dentro del PVC."""
    try:
        init_and_migrate_db()
        conn = sqlite3.connect(str(DB_PATH), timeout=15.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA busy_timeout = 15000")
        now_iso = datetime.now(timezone.utc).isoformat()
        tx_code = f"TX-{int(time.time() * 1000) % 1000000:06d}"

        cursor.execute("PRAGMA table_info(ledger_transactions)")
        columns = [row[1] for row in cursor.fetchall()]

        if "audit_hash" in columns and not IS_V1:
            digest = hashlib.sha256(f"{tx_code}:{concept}:{amount_usd}:{APP_VERSION}".encode()).hexdigest()[:16]
            cursor.execute(
                """
                INSERT INTO ledger_transactions
                (tx_code, concept, amount_usd, app_version, schema_version, pod_origin, created_at, currency, tax_rate, audit_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx_code,
                    concept,
                    amount_usd,
                    APP_VERSION,
                    SCHEMA_VERSION,
                    POD_NAME,
                    now_iso,
                    currency,
                    0.19,
                    digest,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO ledger_transactions
                (tx_code, concept, amount_usd, app_version, schema_version, pod_origin, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx_code,
                    concept,
                    amount_usd,
                    APP_VERSION,
                    SCHEMA_VERSION,
                    POD_NAME,
                    now_iso,
                ),
            )
            digest = "N/A (Esquema V1)"

        conn.commit()
        tx_id = cursor.lastrowid
        conn.close()

        PVC_OPERATIONS_TOTAL.labels(operation="db_insert", status="success").inc()
        DOMAIN_TRANSACTIONS_TOTAL.labels(
            schema_version=SCHEMA_VERSION, version=APP_VERSION, status="committed"
        ).inc()

        return {
            "id": tx_id,
            "tx_code": tx_code,
            "concept": concept,
            "amount_usd": amount_usd,
            "currency": currency,
            "app_version": APP_VERSION,
            "schema_version": SCHEMA_VERSION,
            "audit_hash": digest,
            "pod_origin": POD_NAME,
            "created_at": now_iso,
        }
    except Exception as exc:
        PVC_OPERATIONS_TOTAL.labels(operation="db_insert", status="error").inc()
        DOMAIN_TRANSACTIONS_TOTAL.labels(
            schema_version=SCHEMA_VERSION, version=APP_VERSION, status="failed"
        ).inc()
        return {"error": str(exc)}


def list_transactions(limit: int = 8) -> Dict[str, Any]:
    """Consulta las transacciones almacenadas en el PVC y el estado del esquema."""
    try:
        init_and_migrate_db()
        conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total, COALESCE(SUM(amount_usd), 0) as volume FROM ledger_transactions")
        summary = dict(cursor.fetchone())

        cursor.execute(
            "SELECT * FROM ledger_transactions ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM schema_metadata WHERE key = 'active_schema'")
        meta_row = cursor.fetchone()
        schema_meta = dict(meta_row) if meta_row else {}

        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]

        cursor.execute("PRAGMA table_info(ledger_transactions)")
        columns = [r[1] for r in cursor.fetchall()]
        physical_schema = "schema_v2_migrated" if "audit_hash" in columns else "schema_v1_legacy"

        conn.close()
        db_size_bytes = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        PVC_OPERATIONS_TOTAL.labels(operation="db_select", status="success").inc()
        return {
            "db_connected": True,
            "database_path": str(DB_PATH),
            "database_size_bytes": db_size_bytes,
            "journal_mode": journal_mode,
            "requires_exclusive_lock": True,
            "lock_mechanism": "SQLite BEGIN IMMEDIATE + WAL",
            "total_transactions": summary.get("total", 0),
            "records_persisted": summary.get("total", 0),
            "total_volume_usd": round(summary.get("volume", 0.0), 2),
            "active_schema": physical_schema,
            "column_count": len(columns),
            "schema_metadata": schema_meta,
            "recent_transactions": rows,
        }
    except Exception as exc:
        PVC_OPERATIONS_TOTAL.labels(operation="db_select", status="error").inc()
        return {
            "db_connected": False,
            "database_path": str(DB_PATH),
            "requires_exclusive_lock": True,
            "total_transactions": 0,
            "records_persisted": 0,
            "total_volume_usd": 0.0,
            "active_schema": SCHEMA_VERSION,
            "recent_transactions": [],
            "error": str(exc),
        }


# ==============================================================================
# Inicialización de FastAPI
# ==============================================================================
app = FastAPI(
    title="CoreLedger Recreate Platform",
    description="Microservicio transaccional con persistencia SQLite en PVC, telemetria Prometheus y estrategia Recreate",
    version=APP_VERSION,
)

# Ejecutar inicialización/migración al arrancar el proceso del contenedor
init_and_migrate_db()


# ==============================================================================
# Middleware para Registro de Métricas RED
# ==============================================================================
@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    endpoint = request.url.path
    if endpoint.startswith("/api/"):
        endpoint_label = "/api/*"
    elif endpoint.startswith("/simulate/"):
        endpoint_label = "/simulate/*"
    elif endpoint in ["/", "/healthz", "/ready", "/metrics"]:
        endpoint_label = endpoint
    else:
        endpoint_label = "other"

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint_label,
        status_code=str(response.status_code),
        version=APP_VERSION,
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint_label,
        version=APP_VERSION,
    ).observe(duration)

    return response


# ==============================================================================
# Interfaz Web Interactiva (Dashboard Operativo en /)
# ==============================================================================
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Interfaz visual interactiva de alta fidelidad para inspección de versión, PVC y pruebas."""
    counter_value = get_and_increment_counter()
    db_state = list_transactions(limit=10)
    uptime = int(time.time() - START_TIME)
    active_schema = db_state.get("active_schema", SCHEMA_VERSION)
    db_connected = db_state.get("db_connected", False)
    db_size_kb = round(db_state.get("database_size_bytes", 0) / 1024.0, 1)
    requires_lock = db_state.get("requires_exclusive_lock", True)
    records_persisted = db_state.get("records_persisted", 0)
    col_count = db_state.get("column_count", 8 if IS_V1 else 11)
    journal_mode = db_state.get("journal_mode", "wal").upper()
    total_volume_usd = db_state.get("total_volume_usd", 0.0)

    # Esquema de colores adaptativo según la versión activa
    if IS_V1:
        accent_color = "#3b82f6"       # Azul vibrante (v1.0.0)
        accent_glow = "rgba(59, 130, 246, 0.25)"
        accent_dark = "#1d4ed8"
        version_label = "v1.0.0 (Base Estable)"
    else:
        accent_color = "#10b981"       # Verde esmeralda (v2.0.0)
        accent_glow = "rgba(16, 185, 129, 0.25)"
        accent_dark = "#047857"
        version_label = "v2.0.0 (Migración Activa)"

    tx_rows_html = ""
    for tx in db_state.get("recent_transactions", []):
        audit_val = tx.get("audit_hash") or "MIGRATED_FROM_V1"
        is_tx_v1 = str(tx.get("app_version", "")).startswith("v1")
        pill_cls = "badge-v1" if is_tx_v1 else "badge-v2"
        date_str = str(tx.get("created_at", ""))[:19].replace("T", " ")
        tx_rows_html += f"""
        <tr>
            <td class="font-mono text-cyan">{tx.get('tx_code')}</td>
            <td class="text-muted">{date_str}</td>
            <td class="font-semibold text-white">{tx.get('concept')}</td>
            <td class="font-mono font-bold text-accent">${tx.get('amount_usd'):,.2f} <span class="text-muted text-xs">{tx.get('currency', 'USD')}</span></td>
            <td><span class="version-badge {pill_cls}">{tx.get('app_version')}</span></td>
            <td><span class="schema-tag">{tx.get('schema_version')}</span></td>
            <td class="font-mono text-xs text-muted" title="{audit_val}">{audit_val[:14]}...</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CoreLedger Platform - Estrategia Recreate ({APP_VERSION})</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #0b0f19;
            --bg-card: #111827;
            --bg-card-hover: #162032;
            --bg-input: #1f293d;
            --border-card: #1f293d;
            --border-highlight: #334155;
            --accent: {accent_color};
            --accent-glow: {accent_glow};
            --accent-dark: {accent_dark};
            --text-main: #f9fafb;
            --text-muted: #94a3b8;
            --cyan: #38bdf8;
            --emerald: #10b981;
            --amber: #f59e0b;
            --rose: #f43f5e;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: var(--font-sans);
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            padding-bottom: 40px;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, var(--accent-glow) 0%, transparent 45%);
            background-attachment: fixed;
        }}
        .navbar {{
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-card);
            position: sticky;
            top: 0;
            z-index: 50;
            padding: 12px 24px;
        }}
        .navbar-container {{
            max-width: 1280px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: var(--text-main);
        }}
        .brand-logo {{
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 15px var(--accent-glow);
        }}
        .brand-logo svg {{
            width: 22px;
            height: 22px;
            fill: white;
        }}
        .brand-title {{
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        .brand-title span {{
            color: var(--accent);
        }}
        .nav-links {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .nav-link {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #1e293b;
            color: #cbd5e1;
            border: 1px solid var(--border-highlight);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.2s ease;
        }}
        .nav-link:hover {{
            background: #334155;
            color: #ffffff;
            border-color: var(--accent);
            transform: translateY(-1px);
        }}
        .nav-link.active {{
            background: var(--accent);
            color: #ffffff;
            border-color: var(--accent);
        }}
        .container {{
            max-width: 1280px;
            margin: 24px auto 0 auto;
            padding: 0 20px;
        }}
        /* Hero Section */
        .hero-card {{
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(17, 24, 39, 0.9) 100%);
            border: 1px solid var(--border-card);
            border-top: 4px solid var(--accent);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }}
        .hero-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 14px;
        }}
        .hero-left h1 {{
            font-size: 1.7rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .hero-left p {{
            color: var(--text-muted);
            font-size: 0.94rem;
            max-width: 820px;
            line-height: 1.5;
        }}
        .hero-badges {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .badge-main {{
            background: var(--accent);
            color: #ffffff;
            font-weight: 700;
            font-size: 0.85rem;
            padding: 6px 14px;
            border-radius: 9999px;
            box-shadow: 0 0 12px var(--accent-glow);
            letter-spacing: 0.03em;
        }}
        .badge-sub {{
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-highlight);
            color: #cbd5e1;
            font-family: var(--font-mono);
            font-size: 0.8rem;
            padding: 6px 12px;
            border-radius: 8px;
        }}
        /* Auto Refresh Bar */
        .refresh-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-card);
            padding: 8px 16px;
            border-radius: 8px;
            margin-top: 16px;
            font-size: 0.82rem;
            color: var(--text-muted);
        }}
        .refresh-status {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .pulse-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--emerald);
            box-shadow: 0 0 8px var(--emerald);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.3); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
        .btn-refresh-toggle {{
            background: transparent;
            border: 1px solid var(--border-highlight);
            color: #cbd5e1;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-refresh-toggle:hover {{
            background: #1e293b;
            color: #ffffff;
        }}
        /* Metric Cards Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 12px;
            padding: 18px 20px;
            transition: transform 0.2s ease, border-color 0.2s ease;
            position: relative;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
            border-color: var(--border-highlight);
            background: var(--bg-card-hover);
        }}
        .metric-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .metric-label {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }}
        .metric-icon {{
            font-size: 1.1rem;
            opacity: 0.8;
        }}
        .metric-value {{
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-main);
            letter-spacing: -0.01em;
            word-break: break-all;
            margin-bottom: 4px;
        }}
        .metric-subtext {{
            font-size: 0.78rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        /* Action Center & Toolbar */
        .actions-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
        }}
        .section-title {{
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #f1f5f9;
        }}
        .actions-toolbar {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-family: var(--font-sans);
            font-size: 0.85rem;
            font-weight: 600;
            padding: 9px 16px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-primary {{
            background: var(--accent);
            color: white;
            box-shadow: 0 4px 12px var(--accent-glow);
        }}
        .btn-primary:hover {{
            background: var(--accent-dark);
            transform: translateY(-1px);
        }}
        .btn-secondary {{
            background: #1e293b;
            color: #cbd5e1;
            border: 1px solid var(--border-highlight);
        }}
        .btn-secondary:hover {{
            background: #334155;
            color: white;
            transform: translateY(-1px);
        }}
        .btn-warning {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.4);
        }}
        .btn-warning:hover {{
            background: rgba(245, 158, 11, 0.25);
            transform: translateY(-1px);
        }}
        .btn-danger {{
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.4);
        }}
        .btn-danger:hover {{
            background: rgba(244, 63, 94, 0.25);
            transform: translateY(-1px);
        }}
        /* Console Output Box */
        #console-container {{
            margin-top: 14px;
            display: none;
            background: #090d16;
            border: 1px solid #1e293b;
            border-radius: 8px;
            overflow: hidden;
        }}
        .console-header {{
            background: #111827;
            padding: 8px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1e293b;
            font-size: 0.75rem;
            font-family: var(--font-mono);
            color: var(--text-muted);
        }}
        #console-output {{
            padding: 12px 14px;
            font-family: var(--font-mono);
            font-size: 0.8rem;
            color: #38bdf8;
            max-height: 220px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        /* Table Section */
        .table-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 12px;
            padding: 22px 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        }}
        .table-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 14px;
        }}
        .table-responsive {{
            width: 100%;
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid var(--border-card);
        }}
        table {{
            width: 100%;
            min-width: 820px;
            border-collapse: collapse;
            font-size: 0.84rem;
        }}
        th {{
            background: #0f172a;
            color: var(--text-muted);
            font-size: 0.73rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 12px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border-card);
        }}
        td {{
            padding: 11px 14px;
            border-bottom: 1px solid rgba(31, 41, 61, 0.6);
            vertical-align: middle;
        }}
        tr:hover td {{
            background: rgba(30, 41, 59, 0.4);
        }}
        .font-mono {{ font-family: var(--font-mono); }}
        .font-semibold {{ font-weight: 600; }}
        .font-bold {{ font-weight: 700; }}
        .text-white {{ color: #ffffff; }}
        .text-muted {{ color: var(--text-muted); }}
        .text-cyan {{ color: var(--cyan); }}
        .text-accent {{ color: var(--accent); }}
        .text-xs {{ font-size: 0.72rem; }}
        .version-badge {{
            display: inline-block;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
        }}
        .badge-v1 {{
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }}
        .badge-v2 {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}
        .schema-tag {{
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: #cbd5e1;
            background: #1e293b;
            padding: 3px 8px;
            border-radius: 4px;
        }}
        /* Architectural Callout Banner */
        .callout-box {{
            background: rgba(15, 23, 42, 0.7);
            border-left: 4px solid var(--accent);
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-top: 18px;
            font-size: 0.83rem;
            color: #cbd5e1;
            line-height: 1.5;
        }}
        .callout-box strong {{
            color: #ffffff;
        }}
        /* Modal Form */
        .modal {{
            display: none;
            position: fixed;
            z-index: 100;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
            align-items: center;
            justify-content: center;
        }}
        .modal-content {{
            background: #111827;
            border: 1px solid var(--border-highlight);
            border-radius: 14px;
            width: 90%;
            max-width: 480px;
            padding: 24px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.7);
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}
        .modal-header h3 {{
            font-size: 1.15rem;
            color: white;
        }}
        .close-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.4rem;
            cursor: pointer;
        }}
        .form-group {{
            margin-bottom: 14px;
        }}
        .form-group label {{
            display: block;
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
            text-transform: uppercase;
        }}
        .form-control {{
            width: 100%;
            background: var(--bg-input);
            border: 1px solid var(--border-highlight);
            color: white;
            font-family: var(--font-sans);
            font-size: 0.88rem;
            padding: 9px 12px;
            border-radius: 6px;
            outline: none;
        }}
        .form-control:focus {{
            border-color: var(--accent);
        }}
        /* Footer */
        .footer {{
            margin-top: 32px;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
        .footer p {{
            margin-top: 4px;
            color: #64748b;
        }}
        @media (max-width: 768px) {{
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            .hero-header {{
                flex-direction: column;
            }}
            .actions-toolbar {{
                flex-direction: column;
            }}
            .btn {{
                width: 100%;
                justify-content: center;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar">
        <div class="navbar-container">
            <a href="/" class="brand">
                <div class="brand-logo">
                    <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                </div>
                <div class="brand-title">CoreLedger <span>Cloud-Native</span></div>
            </a>
            <div class="nav-links">
                <a href="http://localhost:3000/d/coreledger-recreate-red-use" target="_blank" class="nav-link" title="Dashboards de Observabilidad y FinOps">
                    <span>📊</span> Grafana
                </a>
                <a href="http://localhost:9090/alerts" target="_blank" class="nav-link" title="Métricas TSDB y Estado de Reglas de Alerta">
                    <span>📈</span> Prometheus
                </a>
                <a href="http://localhost:9093" target="_blank" class="nav-link" title="Gestor de Alarmas Activas">
                    <span>🔔</span> Alertmanager
                </a>
                <a href="http://localhost:5601" target="_blank" class="nav-link" title="Centralización de Logs Filebeat">
                    <span>🔍</span> Kibana (ELK)
                </a>
                <a href="/docs" target="_blank" class="nav-link" title="Especificación OpenAPI Swagger">
                    <span>📑</span> Swagger Docs
                </a>
                <a href="/metrics" target="_blank" class="nav-link" title="Métricas Crudas en Formato Prometheus">
                    <span>⚙️</span> /metrics
                </a>
            </div>
        </div>
    </nav>

    <div class="container">
        <!-- Hero Card -->
        <div class="hero-card">
            <div class="hero-header">
                <div class="hero-left">
                    <h1>
                        CoreLedger Microservice
                        <span class="badge-main">{version_label}</span>
                    </h1>
                    <p>
                        Plataforma transaccional financiera desplegada bajo la estrategia <strong>Recreate</strong>.
                        Garantiza coherencia estricta ACID y prevención de colisiones en base de datos SQLite montada sobre volumen persistente <strong>PVC (ReadWriteOnce)</strong>.
                    </p>
                </div>
                <div class="hero-badges">
                    <span class="badge-sub">Estrategia: RECREATE</span>
                    <span class="badge-sub" id="schema-badge-text">BD: {active_schema} ({col_count} cols)</span>
                </div>
            </div>

            <!-- Auto-refresh status bar -->
            <div class="refresh-bar">
                <div class="refresh-status">
                    <span class="pulse-dot"></span>
                    <span id="auto-refresh-label">Monitoreo en vivo activo (refresco cada 3s)</span>
                </div>
                <div>
                    <button class="btn-refresh-toggle" id="btn-toggle-timer" onclick="toggleAutoRefresh()">Pausar Auto-refresco</button>
                    <button class="btn-refresh-toggle" onclick="fetchLiveStatus()">Actualizar Ahora</button>
                </div>
            </div>
        </div>

        <!-- 6 Responsive Metric Cards -->
        <div class="metrics-grid">
            <!-- Card 1: Pod & Topologia -->
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-label">Pod Activo & Topología</span>
                    <span class="metric-icon">☸️</span>
                </div>
                <div class="metric-value font-mono text-cyan" id="card-pod-name" style="font-size: 0.95rem;">{POD_NAME}</div>
                <div class="metric-subtext">
                    <span>Nodo: <strong>{NODE_NAME}</strong></span> | 
                    <span>IP: <strong>{POD_IP}</strong></span> | 
                    <span>Uptime: <strong id="card-uptime">{uptime}s</strong></span>
                </div>
            </div>

            <!-- Card 2: Estado del Despliegue -->
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-label">Estado de Despliegue</span>
                    <span class="metric-icon">🚀</span>
                </div>
                <div class="metric-value text-emerald" id="card-deploy-status">READY (Recreate)</div>
                <div class="metric-subtext">
                    <span>Estrategia: <strong>Recreate</strong></span> | 
                    <span>HPA: <strong>2 - 6 Réplicas</strong></span>
                </div>
            </div>

            <!-- Card 3: Base de Datos en PVC -->
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-label">Almacenamiento SQLite en PVC</span>
                    <span class="metric-icon">💾</span>
                </div>
                <div class="metric-value" id="card-db-status">
                    {"CONECTADA" if db_connected else "ERROR"} 
                    <span class="text-xs text-muted" id="card-db-size">({db_size_kb} KB)</span>
                </div>
                <div class="metric-subtext">
                    <span>Ruta: <code>/data/recreate_platform.db</code></span> | 
                    <span>Modo: <strong>{journal_mode}</strong></span>
                </div>
            </div>

            <!-- Card 4: Concurrencia y Bloqueo -->
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-label">Control de Concurrencia</span>
                    <span class="metric-icon">🔒</span>
                </div>
                <div class="metric-value text-cyan">BEGIN IMMEDIATE</div>
                <div class="metric-subtext">
                    <span>requires_exclusive_lock: <strong>True</strong></span> | 
                    <span>WAL Concurrency: <strong>Activo</strong></span>
                </div>
            </div>

            <!-- Card 5: Persistencia & Transacciones -->
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-label">Registros Persistidos (PVC)</span>
                    <span class="metric-icon">📊</span>
                </div>
                <div class="metric-value text-accent" id="card-records-count">
                    {records_persisted} transacciones
                </div>
                <div class="metric-subtext">
                    <span>Volumen: <strong id="card-volume-usd">${total_volume_usd:,.2f} USD</strong></span> | 
                    <span>Reqs: <strong id="card-counter">{counter_value}</strong></span>
                </div>
            </div>

            <!-- Card 6: Esquema Relacional -->
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-label">Esquema Relacional en Disco</span>
                    <span class="metric-icon">🗄️</span>
                </div>
                <div class="metric-value font-mono" id="card-schema-val" style="font-size: 0.95rem;">{active_schema}</div>
                <div class="metric-subtext">
                    <span>Estructura: <strong id="card-col-count">{col_count} Columnas</strong></span> | 
                    <span>Migración: <strong>Serializada</strong></span>
                </div>
            </div>
        </div>

        <!-- Action Center & Lab Controls -->
        <div class="actions-card">
            <div class="section-title">
                <span>⚡</span> Centro de Control y Pruebas en Vivo
            </div>
            <div class="actions-toolbar">
                <button class="btn btn-primary" onclick="openTxModal()">
                    <span>➕</span> Nueva Transacción en PVC
                </button>
                <button class="btn btn-secondary" onclick="createQuickTransaction()">
                    <span>🎲</span> Transacción Rápida
                </button>
                <button class="btn btn-secondary" onclick="verifySso()">
                    <span>🔑</span> Probar SSO / MFA
                </button>
                <button class="btn btn-warning" onclick="triggerCpu()">
                    <span>🔥</span> Simular Carga CPU (HPA)
                </button>
                <button class="btn btn-danger" onclick="triggerError()">
                    <span>⚠️</span> Simular HTTP 500 (Alerta)
                </button>
            </div>

            <!-- Interactive Console Output -->
            <div id="console-container">
                <div class="console-header">
                    <span id="console-title">Respuesta del Microservicio</span>
                    <button class="btn-refresh-toggle" onclick="document.getElementById('console-container').style.display='none'">Cerrar</button>
                </div>
                <div id="console-output"></div>
            </div>
        </div>

        <!-- Persisted Transactions Ledger Table -->
        <div class="table-card">
            <div class="table-header">
                <div>
                    <div class="section-title" style="margin-bottom: 4px;">
                        <span>📜</span> Libro Contable Persistido en PVC (RWO)
                    </div>
                    <p class="text-muted text-xs">
                        Registros alojados en <code>/data/recreate_platform.db</code>. Sobreviven completamente al apagado de pods durante la estrategia <strong>Recreate</strong>.
                    </p>
                </div>
                <div class="text-muted text-xs font-mono">
                    Total Registros: <strong class="text-accent" id="table-total-count">{records_persisted}</strong>
                </div>
            </div>

            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Código TX</th>
                            <th>Fecha y Hora (UTC)</th>
                            <th>Concepto</th>
                            <th>Monto</th>
                            <th>Versión App</th>
                            <th>Esquema BD</th>
                            <th>Hash Auditoría</th>
                        </tr>
                    </thead>
                    <tbody id="tx-tbody">
                        {tx_rows_html}
                    </tbody>
                </table>
            </div>

            <div class="callout-box">
                <strong>¿Por qué la Estrategia Recreate es mandatoria aquí?</strong><br>
                El almacenamiento SQLite es un motor embebido basado en un archivo local. A diferencia de motores cliente-servidor (PostgreSQL/MySQL), no soporta múltiples escritores concurrentes compitiendo sobre un PVC con bloqueo POSIX.
                Con <code>RollingUpdate</code>, réplicas viejas y nuevas intentarían acceder simultáneamente al archivo durante la migración estructural, provocando excepciones <code>OperationalError: database is locked</code> o inconsistencias irreversibles. 
                <strong>Recreate</strong> garantiza que Kubernetes termine ordenadamente todos los pods viejos antes de iniciar los nuevos y ejecutar la migración <code>ALTER TABLE</code> de forma estrictamente serializada.
            </div>
        </div>

        <!-- Modal para Nueva Transacción -->
        <div id="tx-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Registrar Transacción en SQLite</h3>
                    <button class="close-btn" onclick="closeTxModal()">&times;</button>
                </div>
                <form id="tx-form" onsubmit="handleTxSubmit(event)">
                    <div class="form-group">
                        <label>Concepto de Transacción</label>
                        <input type="text" id="tx-concept" class="form-control" required placeholder="Ej. Pago de Servicios Cloud AWS/GCP" value="Operacion contable desde Dashboard Web">
                    </div>
                    <div class="form-group">
                        <label>Monto (USD)</label>
                        <input type="number" id="tx-amount" class="form-control" step="0.01" min="1" required value="250.00">
                    </div>
                    <div class="form-group">
                        <label>Moneda</label>
                        <input type="text" id="tx-currency" class="form-control" value="USD" readonly>
                    </div>
                    <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px;">
                        <button type="button" class="btn btn-secondary" onclick="closeTxModal()">Cancelar</button>
                        <button type="submit" class="btn btn-primary">Guardar en PVC</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div><strong>Universidad — Plataformas II: Demostración de Estrategia Recreate en Kubernetes</strong></div>
            <p>Integrantes: Esteban Guarín Valencia & Juan José Arias Gallego | Clúster: Minikube Docker (6 CPUs, 10 GiB RAM)</p>
        </div>
    </div>

    <script>
        let autoRefreshInterval = null;
        let isAutoRefreshActive = true;

        function showConsole(title, data) {{
            const container = document.getElementById('console-container');
            const titleEl = document.getElementById('console-title');
            const outEl = document.getElementById('console-output');
            titleEl.textContent = title;
            outEl.textContent = JSON.stringify(data, null, 2);
            container.style.display = 'block';
        }}

        async function fetchLiveStatus() {{
            try {{
                const res = await fetch('/api/info');
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const info = await res.json();
                
                // Actualizar contadores y tarjetas
                document.getElementById('card-counter').textContent = info.counter;
                document.getElementById('card-uptime').textContent = Math.round(info.uptime_seconds) + 's';
                document.getElementById('card-records-count').textContent = info.database.records_persisted + ' transacciones';
                document.getElementById('table-total-count').textContent = info.database.records_persisted;
                document.getElementById('card-volume-usd').textContent = '$' + Number(info.database.total_volume_usd || 0).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + ' USD';
                document.getElementById('card-schema-val').textContent = info.database.active_schema;
                document.getElementById('card-col-count').textContent = info.database.column_count + ' Columnas';
                document.getElementById('schema-badge-text').textContent = 'BD: ' + info.database.active_schema + ' (' + info.database.column_count + ' cols)';

                // Refrescar tabla de transacciones
                await refreshTable();
            }} catch (err) {{
                console.warn('Error consultando /api/info (posible corte Recreate):', err);
            }}
        }}

        async function refreshTable() {{
            try {{
                const res = await fetch('/api/transactions?limit=10');
                if (!res.ok) return;
                const data = await res.json();
                const tbody = document.getElementById('tx-tbody');
                if (data.recent_transactions && data.recent_transactions.length > 0) {{
                    tbody.innerHTML = data.recent_transactions.map(tx => {{
                        const isV1 = String(tx.app_version || '').startsWith('v1');
                        const badgeCls = isV1 ? 'badge-v1' : 'badge-v2';
                        const auditVal = tx.audit_hash || 'MIGRATED_FROM_V1';
                        const dateStr = String(tx.created_at || '').substring(0, 19).replace('T', ' ');
                        return `
                            <tr>
                                <td class="font-mono text-cyan">${{tx.tx_code}}</td>
                                <td class="text-muted">${{dateStr}}</td>
                                <td class="font-semibold text-white">${{tx.concept}}</td>
                                <td class="font-mono font-bold text-accent">$${{Number(tx.amount_usd).toLocaleString('en-US', {{minimumFractionDigits: 2}})}} <span class="text-muted text-xs">${{tx.currency || 'USD'}}</span></td>
                                <td><span class="version-badge ${{badgeCls}}">${{tx.app_version}}</span></td>
                                <td><span class="schema-tag">${{tx.schema_version}}</span></td>
                                <td class="font-mono text-xs text-muted" title="${{auditVal}}">${{auditVal.substring(0, 14)}}...</td>
                            </tr>
                        `;
                    }}).join('');
                }}
            }} catch (e) {{
                console.warn('Error al actualizar tabla:', e);
            }}
        }}

        function toggleAutoRefresh() {{
            const btn = document.getElementById('btn-toggle-timer');
            const label = document.getElementById('auto-refresh-label');
            if (isAutoRefreshActive) {{
                clearInterval(autoRefreshInterval);
                isAutoRefreshActive = false;
                btn.textContent = 'Reanudar Auto-refresco';
                label.textContent = 'Monitoreo en vivo pausado';
            }} else {{
                autoRefreshInterval = setInterval(fetchLiveStatus, 3000);
                isAutoRefreshActive = true;
                btn.textContent = 'Pausar Auto-refresco';
                label.textContent = 'Monitoreo en vivo activo (refresco cada 3s)';
            }}
        }}

        function openTxModal() {{
            document.getElementById('tx-modal').style.display = 'flex';
        }}

        function closeTxModal() {{
            document.getElementById('tx-modal').style.display = 'none';
        }}

        async function handleTxSubmit(e) {{
            e.preventDefault();
            const concept = document.getElementById('tx-concept').value;
            const amount = parseFloat(document.getElementById('tx-amount').value);
            const currency = document.getElementById('tx-currency').value;
            closeTxModal();

            try {{
                const res = await fetch('/api/transactions', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ concept, amount_usd: amount, currency }})
                }});
                const data = await res.json();
                showConsole('Transacción guardada exitosamente en SQLite PVC:', data);
                await fetchLiveStatus();
            }} catch (err) {{
                showConsole('Error registrando transacción:', {{ error: err.message }});
            }}
        }}

        async function createQuickTransaction() {{
            const concepts = [
                'Facturación de Servicios Cloud Kubernetes',
                'Liquidación de Nómina DevSecOps',
                'Compra de Licencias de Observabilidad',
                'Transferencia Interbancaria SWIFT',
                'Auditoría y Conciliación Financiera'
            ];
            const randomConcept = concepts[Math.floor(Math.random() * concepts.length)];
            const randomAmount = Math.round((50 + Math.random() * 950) * 100) / 100;

            try {{
                const res = await fetch('/api/transactions', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        concept: randomConcept,
                        amount_usd: randomAmount,
                        currency: 'USD'
                    }})
                }});
                const data = await res.json();
                showConsole('Transacción Rápida Registrada en PVC (/data/recreate_platform.db):', data);
                await fetchLiveStatus();
            }} catch (err) {{
                showConsole('Error en transacción rápida:', {{ error: err.message }});
            }}
        }}

        async function verifySso() {{
            try {{
                const tokRes = await fetch('/api/auth/token', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ username: 'esteban.guarin@universidad.edu.co', mfa_code: '482910' }})
                }});
                const tokData = await tokRes.json();
                const verRes = await fetch('/api/auth/verify', {{
                    method: 'POST',
                    headers: {{'Authorization': 'Bearer ' + tokData.access_token}}
                }});
                const verData = await verRes.json();
                showConsole('Verificación SSO / OIDC + MFA Validada:', {{
                    issued_token: tokData,
                    verification_result: verData
                }});
            }} catch (err) {{
                showConsole('Error en verificación SSO:', {{ error: err.message }});
            }}
        }}

        async function triggerCpu() {{
            showConsole('Iniciando ciclo de estrés de CPU por 1.5 segundos para elevar métrica USE...', {{ status: 'running' }});
            try {{
                const res = await fetch('/simulate/cpu-load?seconds=1.5');
                const data = await res.json();
                showConsole('Ciclo de CPU finalizado (Revisar en Grafana métricas USE):', data);
            }} catch (err) {{
                showConsole('Error en ciclo de CPU:', {{ error: err.message }});
            }}
        }}

        async function triggerError() {{
            try {{
                const res = await fetch('/simulate/error?status_code=500');
                const data = await res.json();
                showConsole('Fallo HTTP 500 simulado (Impacta métricas RED y alerta HighHttp5xxErrorRate):', data);
            }} catch (err) {{
                showConsole('Error simulando fallo:', {{ error: err.message }});
            }}
        }}

        // Iniciar temporizador automático de actualización
        autoRefreshInterval = setInterval(fetchLiveStatus, 3000);
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


# ==============================================================================
# Endpoints de API de Dominio y Estado Persistente
# ==============================================================================
@app.get("/api/info", response_class=JSONResponse)
async def api_info() -> Dict[str, Any]:
    """Retorna los metadatos de la aplicación, contador y estado de la base de datos en PVC."""
    db_state = list_transactions(limit=3)
    return {
        "version": APP_VERSION,
        "schema_version": db_state.get("active_schema", SCHEMA_VERSION),
        "deployment_strategy": "Recreate",
        "db_connected": db_state.get("db_connected", False),
        "requires_exclusive_lock": db_state.get("requires_exclusive_lock", True),
        "environment": APP_ENV,
        "pod_name": POD_NAME,
        "pod_ip": POD_IP,
        "node_name": NODE_NAME,
        "uptime_seconds": int(time.time() - START_TIME),
        "persistent_counter": get_and_increment_counter(),
        "total_transactions": db_state.get("total_transactions", 0),
        "records_persisted": db_state.get("records_persisted", 0),
        "total_volume_usd": db_state.get("total_volume_usd", 0.0),
    }


@app.get("/api/transactions", response_class=JSONResponse)
async def get_transactions(limit: int = 10) -> Dict[str, Any]:
    """Devuelve el historial de transacciones persistidas en SQLite dentro del PVC."""
    return list_transactions(limit=min(max(limit, 1), 50))


@app.post("/api/transactions", response_class=JSONResponse, status_code=status.HTTP_201_CREATED)
async def post_transaction(payload: TransactionInput) -> Dict[str, Any]:
    """Registra una nueva transacción en la base de datos SQLite alojada en el volumen PVC."""
    result = record_transaction(
        concept=payload.concept,
        amount_usd=payload.amount_usd,
        currency=payload.currency or "USD",
    )
    return result


@app.get("/api/schema-status", response_class=JSONResponse)
async def get_schema_status() -> Dict[str, Any]:
    """Inspecciona el estado de migración del esquema de base de datos en el PVC."""
    db_state = list_transactions(limit=1)
    return {
        "app_version": APP_VERSION,
        "active_schema": db_state.get("active_schema", SCHEMA_VERSION),
        "db_connected": db_state.get("db_connected", False),
        "requires_exclusive_lock": True,
        "lock_mechanism": db_state.get("lock_mechanism", "SQLite BEGIN IMMEDIATE + WAL"),
        "deployment_strategy": "Recreate",
        "database_path": str(DB_PATH),
        "database_size_bytes": db_state.get("database_size_bytes", 0),
        "journal_mode": db_state.get("journal_mode", "wal"),
        "schema_metadata": db_state.get("schema_metadata", {}),
        "records_persisted": db_state.get("records_persisted", 0),
        "total_records_persisted": db_state.get("total_transactions", 0),
    }


# ==============================================================================
# Sondas de Salud de Kubernetes (Liveness y Readiness)
# ==============================================================================
@app.get("/healthz", response_class=JSONResponse)
async def healthz():
    """Sonda de Actividad (livenessProbe): verifica si el proceso está vivo."""
    return {"status": "alive", "version": APP_VERSION, "timestamp": time.time()}


@app.get("/ready", response_class=JSONResponse)
async def ready():
    """Sonda de Preparación (readinessProbe): verifica acceso al PVC y disponibilidad."""
    db_ok = DB_PATH.exists() or DATA_DIR.exists()
    return {
        "status": "ready" if db_ok else "degraded",
        "version": APP_VERSION,
        "schema_version": SCHEMA_VERSION,
        "pvc_mounted": db_ok,
    }


# ==============================================================================
# Endpoints de Autenticación SSO / OIDC + MFA
# ==============================================================================
@app.post("/api/auth/token", response_class=JSONResponse)
async def issue_auth_token(payload: AuthTokenRequest):
    """Emite un token firmado simulando proveedor de identidad centralizado (OIDC/SSO + MFA)."""
    if len(payload.mfa_code.strip()) < 6:
        AUTH_EVENTS_TOTAL.labels(operation="token_issue", result="mfa_rejected").inc()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"authenticated": False, "error": "Codigo MFA invalido"},
        )

    raw_seed = f"{payload.username}:{payload.mfa_code}:{APP_VERSION}:recreate-sso"
    token_hash = hashlib.sha256(raw_seed.encode()).hexdigest()
    AUTH_EVENTS_TOTAL.labels(operation="token_issue", result="success").inc()
    return {
        "access_token": f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{token_hash[:32]}",
        "token_type": "Bearer",
        "expires_in": 3600,
        "mfa_verified": True,
        "subject": payload.username,
        "issuer": "https://sso.recreate.local/oidc",
    }


@app.post("/api/auth/verify", response_class=JSONResponse)
async def auth_verify(request: Request):
    """Valida el token Bearer emitido por el flujo SSO/OIDC."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if len(token) >= 10:
            AUTH_EVENTS_TOTAL.labels(operation="token_verify", result="valid").inc()
            return {
                "authenticated": True,
                "mechanism": "Single-Sign-On (SSO) / OIDC + MFA",
                "token_valid": True,
                "user": "esteban.guarin@universidad.edu.co",
                "role": "Platform Engineer",
                "schema_access": SCHEMA_VERSION,
            }
    AUTH_EVENTS_TOTAL.labels(operation="token_verify", result="unauthorized").inc()
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"authenticated": False, "error": "Token Bearer de autenticacion requerido"},
    )


# ==============================================================================
# Endpoint de Métricas Prometheus
# ==============================================================================
@app.get("/metrics")
async def metrics():
    """Endpoint oficial de scrape para Prometheus."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ==============================================================================
# Endpoints de Simulación para Pruebas de HPA y Alarmas
# ==============================================================================
@app.get("/simulate/cpu-load")
async def simulate_cpu_load(seconds: float = 1.0):
    """Genera consumo de CPU sintético para disparar métricas y probar el HPA."""
    end_time = time.time() + min(seconds, 5.0)
    while time.time() < end_time:
        _ = [x ** 2 for x in range(2000)]
    return {
        "message": "Carga de CPU ejecutada satisfactoriamente",
        "duration_seconds": seconds,
        "pod": POD_NAME,
    }


@app.get("/simulate/error")
async def simulate_error(status_code: int = 500):
    """Genera errores HTTP controlados (500, 502, 503) para probar alarmas de tasa de error."""
    valid_status = status_code if status_code in [500, 502, 503, 504] else 500
    return JSONResponse(
        status_code=valid_status,
        content={"error": f"Fallo simulado con código HTTP {valid_status}", "pod": POD_NAME},
    )


@app.get("/simulate/latency")
async def simulate_latency(delay: float = 1.5):
    """Introduce latencia artificial para disparar alertas de degradación de respuesta."""
    sleep_time = min(max(delay, 0.1), 5.0)
    time.sleep(sleep_time)
    return {"message": "Respuesta con latencia completada", "delay_seconds": sleep_time}
