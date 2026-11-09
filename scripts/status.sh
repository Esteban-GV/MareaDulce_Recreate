#!/usr/bin/env bash
# ==============================================================================
# Script de Estado Consolidado y Diagnóstico (status.sh)
# Plataforma: Marea Dulce Cloud-Native (Kubernetes Recreate Stack)
# Uso:
#   ./scripts/status.sh             -> Muestra el estado operativo consolidado
#   ./scripts/status.sh --reset-v1  -> Respalda SQLite (.backup) y restablece a v1.0.0
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ "${1:-}" == "--reset-v1" ]]; then
    echo "=============================================================================="
    echo " REINICIO CONTROLADO A v1.0.0 CON RESPALDO SQLITE PREVIO"
    echo "=============================================================================="
    POD=$(kubectl get pod -n recreate-lab -l app.kubernetes.io/name=marea-app -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "${POD}" ]]; then
        echo "[1/3] Ejecutando respaldo en caliente (.backup) en Pod ${POD}..."
        kubectl exec -n recreate-lab "${POD}" -- python3 -c '
import sqlite3, time
from pathlib import Path

bkp_dir = Path("/data/backups")
bkp_dir.mkdir(parents=True, exist_ok=True)
ts = int(time.time())
src_path = "/data/marea_dulce.db"
bkp_path = f"/data/backups/marea_dulce_{ts}.db"

src = sqlite3.connect(src_path, timeout=10.0)
bkp = sqlite3.connect(bkp_path)
with bkp:
    src.backup(bkp)
integrity = bkp.execute("PRAGMA integrity_check").fetchone()[0]
bkp.close()
src.close()
print(f"  -> Respaldo verificado: {bkp_path} (integrity_check={integrity})")
'
    fi

    echo "[2/3] Aplicando manifiesto k8s/deployment-v1.yaml y esperando rollout..."
    kubectl apply -f "${REPO_ROOT}/k8s/deployment-v1.yaml"
    kubectl rollout status deployment/marea-app-deployment -n recreate-lab --timeout=120s

    echo "[3/3] Verificando salud en v1.0.0..."
    kubectl get pods -n recreate-lab -l app.kubernetes.io/name=marea-app -o wide
    echo "=============================================================================="
    echo " Plataforma lista en v1.0.0 para repetir la demostración."
    echo "=============================================================================="
    exit 0
fi

echo "=============================================================================="
echo " ESTADO CONSOLIDADO — MAREA DULCE (ESTRATEGIA RECREATE)"
echo "=============================================================================="

echo ""
echo "[1/6] Nodos del Clúster:"
kubectl get nodes -o wide

echo ""
echo "[2/6] Estrategia e Imagen Activa del Deployment (namespace: recreate-lab):"
STRATEGY=$(kubectl get deployment marea-app-deployment -n recreate-lab -o jsonpath='{.spec.strategy.type}' 2>/dev/null || echo "NO_DESPLEGADO")
IMAGE=$(kubectl get deployment marea-app-deployment -n recreate-lab -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "N/A")
APP_VER=$(kubectl get deployment marea-app-deployment -n recreate-lab -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="APP_VERSION")].value}' 2>/dev/null || echo "N/A")
echo "  -> Deployment:            marea-app-deployment"
echo "  -> Estrategia configurada: ${STRATEGY}"
echo "  -> Imagen activa:          ${IMAGE} (APP_VERSION=${APP_VER})"
kubectl get deployment marea-app-deployment -n recreate-lab -o wide 2>/dev/null || true

echo ""
echo "[3/6] Estado de Pods y ReplicaSets en 'recreate-lab':"
kubectl get pods,rs -n recreate-lab -o wide

echo ""
echo "[4/6] Almacenamiento Persistente (PVC ReadWriteOnce):"
kubectl get pvc -n recreate-lab

echo ""
echo "[5/6] Red, Ingress y Aislamiento (NetworkPolicy):"
kubectl get svc,ingress,networkpolicy -n recreate-lab

echo ""
echo "[6/6] Stack de Observabilidad (Monitoring & Metrics):"
kubectl get pods -n monitoring
echo ""
kubectl get servicemonitor,prometheusrule -n recreate-lab 2>/dev/null || echo "CRDs de Prometheus Operator no registrados aún."

echo ""
echo "=============================================================================="
echo " Verificación de estado finalizada."
echo "=============================================================================="
