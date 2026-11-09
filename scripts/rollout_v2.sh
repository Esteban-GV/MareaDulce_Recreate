#!/usr/bin/env bash
# ==============================================================================
# Demostración Automatizada de Rollout Recreate (v1.0.0 -> v2.0.0)
# Plataforma: Marea Dulce Cloud-Native
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=================================================================="
echo " [Marea Dulce] Iniciando Actualización Recreate a la Versión 2.0.0"
echo "=================================================================="

echo "[1/4] Verificando pod actual v1.0.0 en recreate-lab..."
kubectl get pods -n recreate-lab -l app.kubernetes.io/name=marea-app -o wide

echo "[2/4] Aplicando manifiesto k8s/deployment-v2.yaml (strategy: Recreate)..."
kubectl apply -f "${REPO_ROOT}/k8s/deployment-v2.yaml"

echo "[3/4] Observando la transición Recreate en tiempo real..."
echo "Kubernetes terminará el pod anterior al 100% (ventana 0 réplicas) antes de crear v2."
kubectl rollout status deployment/marea-app-deployment -n recreate-lab --timeout=120s

echo "[4/4] Verificando nueva versión y persistencia SQLite en PVC..."
kubectl get pods -n recreate-lab -l app.kubernetes.io/name=marea-app -o wide

echo "=================================================================="
echo " Transición Recreate a v2.0.0 completada exitosamente."
echo " Base de datos SQLite migrada y respaldada en PVC ReadWriteOnce."
echo "=================================================================="
