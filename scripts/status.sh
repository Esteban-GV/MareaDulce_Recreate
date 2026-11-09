#!/usr/bin/env bash
# ==============================================================================
# Script de Estado Consolidado y Reinicio Reproducible a v1.0.0 (status.sh)
# Uso:
#   ./scripts/status.sh             -> Muestra el estado operativo consolidado
#   ./scripts/status.sh --reset-v1  -> Respalda SQLite (.backup), revierte esquema
#                                      a schema_v1_legacy y despliega v1.0.0
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ "${1:-}" == "--reset-v1" ]]; then
    echo "=============================================================================="
    echo " REINICIO CONTROLADO A v1.0.0 (ESQUEMA LEGADO) CON RESPALDO SQLITE PREVIO"
    echo "=============================================================================="
    POD=$(kubectl get pod -n recreate-lab -l app.kubernetes.io/name=recreate-app -o jsonpath='{.items[0].metadata.name}')
    echo "[1/3] Ejecutando respaldo en caliente (.backup) en Pod ${POD}..."
    kubectl exec -n recreate-lab "${POD}" -- python3 -c '
import sqlite3, time
from pathlib import Path

bkp_dir = Path("/data/backups")
bkp_dir.mkdir(parents=True, exist_ok=True)
ts = int(time.time())
src_path = "/data/recreate_platform.db"
bkp_path = f"/data/backups/recreate_platform_{ts}.db"

src = sqlite3.connect(src_path, timeout=10.0)
bkp = sqlite3.connect(bkp_path)
with bkp:
    src.backup(bkp)
integrity = bkp.execute("PRAGMA integrity_check").fetchone()[0]
bkp.close()
src.close()
print(f"  -> Respaldo verificado: {bkp_path} (integrity_check={integrity})")
'
    echo "[2/3] Aplicando manifiesto k8s/deployment-v1.yaml y esperando rollout..."
    kubectl apply -f "${REPO_ROOT}/k8s/deployment-v1.yaml"
    kubectl rollout status deployment/recreate-app-deployment -n recreate-lab --timeout=90s

    NEW_POD=$(kubectl get pod -n recreate-lab -l app.kubernetes.io/name=recreate-app -o jsonpath='{.items[0].metadata.name}')
    echo "[3/3] Reconstruyendo estructura pura de 8 columnas (schema_v1_legacy) conservando registros..."
    kubectl exec -n recreate-lab "${NEW_POD}" -- python3 -c '
import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect("/data/recreate_platform.db", timeout=10.0)
cur = conn.cursor()
cur.execute("PRAGMA table_info(ledger_transactions)")
cols = [r[1] for r in cur.fetchall()]
if "audit_hash" in cols:
    cur.execute("""
        CREATE TABLE ledger_transactions_v1_clean (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_code TEXT NOT NULL,
            concept TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            app_version TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            pod_origin TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT INTO ledger_transactions_v1_clean
        (id, tx_code, concept, amount_usd, app_version, schema_version, pod_origin, created_at)
        SELECT id, tx_code, concept, amount_usd, app_version, '\''schema_v1_legacy'\'', pod_origin, created_at
        FROM ledger_transactions
    """)
    cur.execute("DROP TABLE ledger_transactions")
    cur.execute("ALTER TABLE ledger_transactions_v1_clean RENAME TO ledger_transactions")

now_iso = datetime.now(timezone.utc).isoformat()
cur.execute("""
    INSERT INTO schema_metadata (key, value, updated_at, updated_by_pod)
    VALUES ('\''active_schema'\'', '\''schema_v1_legacy'\'', ?, '\''reset-v1-script'\'')
    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at, updated_by_pod=excluded.updated_by_pod
""", (now_iso,))
conn.commit()
cur.execute("PRAGMA table_info(ledger_transactions)")
final_cols = [r[1] for r in cur.fetchall()]
count = cur.execute("SELECT COUNT(*) FROM ledger_transactions").fetchone()[0]
conn.close()
print(f"  -> Esquema restaurado a schema_v1_legacy. Filas conservadas: {count}. Columnas: {final_cols}")
'
    echo "=============================================================================="
    echo " Plataforma lista en v1.0.0 (schema_v1_legacy) para repetir la demostración."
    echo "=============================================================================="
    exit 0
fi

echo "=============================================================================="
echo " ESTADO CONSOLIDADO DE LA PLATAFORMA KUBERNETES (ESTRATEGIA RECREATE)"
echo "=============================================================================="

echo ""
echo "[1/7] Contexto y Nodos del Clúster:"
kubectl get nodes -o wide

echo ""
echo "[2/7] Estrategia e Imagen Activa del Deployment (namespace: recreate-lab):"
STRATEGY=$(kubectl get deployment recreate-app-deployment -n recreate-lab -o jsonpath='{.spec.strategy.type}' 2>/dev/null || echo "NO_DESPLEGADO")
IMAGE=$(kubectl get deployment recreate-app-deployment -n recreate-lab -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "N/A")
APP_VER=$(kubectl get deployment recreate-app-deployment -n recreate-lab -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="APP_VERSION")].value}' 2>/dev/null || echo "N/A")
echo "  -> Deployment:            recreate-app-deployment"
echo "  -> Estrategia configurada: ${STRATEGY}"
echo "  -> Imagen activa:          ${IMAGE} (APP_VERSION=${APP_VER})"
kubectl get deployment recreate-app-deployment -n recreate-lab -o wide 2>/dev/null || true

echo ""
echo "[3/7] Estado de Pods y ReplicaSets en 'recreate-lab':"
kubectl get pods,rs -n recreate-lab -o wide

echo ""
echo "[4/7] Almacenamiento Persistente (PVC) y Autoescalado (HPA):"
kubectl get pvc,hpa -n recreate-lab

echo ""
echo "[5/7] Red, Ingress y Aislamiento (NetworkPolicy):"
kubectl get svc,ingress,networkpolicy -n recreate-lab

echo ""
echo "[6/7] Recursos del Operador Prometheus (ServiceMonitor y PrometheusRule):"
kubectl get servicemonitor,prometheusrule -n recreate-lab 2>/dev/null || echo "CRDs de Prometheus Operator no encontrados."

echo ""
echo "[7/7] Estado del Stack de Observabilidad (namespace: monitoring):"
kubectl get pods -n monitoring

echo ""
echo "=============================================================================="
echo " Verificación de estado finalizada."
echo "=============================================================================="
