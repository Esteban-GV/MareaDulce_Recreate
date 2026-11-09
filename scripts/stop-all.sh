#!/usr/bin/env bash
# ==============================================================================
# CoreLedger Cloud-Native Platform — stop-all.sh
# Propósito: Escalar a cero las réplicas de la aplicación o detener el clúster.
#            Opciones: --scale-zero (por defecto), --cluster, --dry-run.
# Uso:       bash scripts/stop-all.sh [--scale-zero | --cluster | --dry-run]
# ==============================================================================
set -euo pipefail

# Auto-activación de pertenencia al grupo docker si la sesión actual no lo tiene activo
if ! docker ps >/dev/null 2>&1; then
  if grep -q "^docker:.*\<${USER:-$(id -un)}\>" /etc/group 2>/dev/null; then
    echo "[AUTO-FIX] Sesión sin grupo 'docker' activo en terminal actual. Re-ejecutando con newgrp docker..."
    exec newgrp docker -c "bash \"$0\" $*"
  fi
fi

MODE="${1:---scale-zero}"

echo "=================================================================="
echo " [CoreLedger] Deteniendo Cargas de Trabajo (modo: ${MODE})"
echo "=================================================================="

if [ "${MODE}" = "--cluster" ]; then
  echo "Deteniendo túneles locales activos..."
  pkill -f "kubectl port-forward" 2>/dev/null || true
  echo "Deteniendo clúster Minikube..."
  minikube stop
  echo "[CoreLedger] Clúster Minikube detenido."
elif [ "${MODE}" = "--scale-zero" ]; then
  echo "Escalando deployment recreate-app-deployment a 0 réplicas..."
  kubectl scale deployment/recreate-app-deployment --replicas=0 -n recreate-lab || true
  echo "[CoreLedger] Réplicas escaladas a 0. Datos en PVC (/data) intactos."
else
  echo "Modo seguro (--dry-run) verificado. Uso: bash scripts/stop-all.sh [--scale-zero | --cluster | --dry-run]"
fi
