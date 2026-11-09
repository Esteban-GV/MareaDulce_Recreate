#!/usr/bin/env bash
# ==============================================================================
# CoreLedger Cloud-Native Platform — restart-all.sh
# Propósito: Reconciliar manifiestos y ejecutar un reinicio controlado bajo la
#            estrategia Recreate sobre recreate-app-deployment.
# Uso:       bash scripts/restart-all.sh
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================================="
echo " [CoreLedger] Reconciliando y Reiniciando Cargas de Trabajo"
echo "=================================================================="

bash "${SCRIPT_DIR}/start-all.sh"

echo "[Restart] Ejecutando rollout restart en recreate-app-deployment..."
kubectl rollout restart deployment/recreate-app-deployment -n recreate-lab
kubectl rollout status deployment/recreate-app-deployment -n recreate-lab --timeout=90s

echo "=================================================================="
echo " [CoreLedger] Reinicio Recreate completado exitosamente."
echo "=================================================================="
