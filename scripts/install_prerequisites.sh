#!/usr/bin/env bash
# ==============================================================================
# Script de Instalación y Verificación de Requisitos Previos (EndeavourOS / Arch)
# Proyecto: k8s-recreate-deployment (Plataformas II)
# ==============================================================================

set -euo pipefail

echo "=== Verificando dependencias del sistema ==="

PACKAGES=(docker docker-buildx minikube kubectl helm)
MISSING_PKGS=()

for pkg in "${PACKAGES[@]}"; do
    if ! command -v "$pkg" &>/dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done

if [ ${#MISSING_PKGS[@]} -eq 0 ]; then
    echo "Todas las herramientas principales están instaladas: ${PACKAGES[*]}"
else
    echo "Paquetes faltantes detectados: ${MISSING_PKGS[*]}"
    echo "Instalando mediante pacman (requiere privilegios sudo)..."
    sudo pacman -S --needed --noconfirm "${MISSING_PKGS[@]}"
fi

echo "=== Verificando estado del demonio Docker ==="
if ! systemctl is-active --quiet docker; then
    echo "Iniciando y habilitando servicio docker..."
    sudo systemctl enable --now docker
fi

echo "=== Verificando permisos de grupo Docker ==="
if ! groups "$USER" | grep -q '\bdocker\b'; then
    echo "Añadiendo al usuario $USER al grupo docker..."
    sudo usermod -aG docker "$USER"
    echo "IMPORTANTE: Para aplicar los permisos sin cerrar sesión, ejecute: newgrp docker"
fi

echo "=== Estado operativo verificado satisfactoriamente ==="

