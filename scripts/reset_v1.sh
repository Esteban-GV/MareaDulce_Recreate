#!/usr/bin/env bash
# ==============================================================================
# Reinicio Reproducible de Demostración a Versión 1.0.0
# Plataforma: Marea Dulce Cloud-Native
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=================================================================="
echo " [Marea Dulce] Restableciendo Despliegue a Versión 1.0.0"
echo "=================================================================="

kubectl apply -f "${REPO_ROOT}/k8s/deployment-v1.yaml"
kubectl rollout status deployment/marea-app-deployment -n recreate-lab --timeout=120s

echo "=================================================================="
echo " Plataforma restablecida a v1.0.0. Lista para una nueva demostración."
echo "=================================================================="
