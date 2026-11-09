#!/usr/bin/env bash
# ==============================================================================
# Marea Dulce Cloud-Native Platform — benchmark.sh
# Propósito: Ejecutar pruebas sintéticas de rendimiento y fiabilidad HTTP
#            contra los endpoints críticos del microservicio Marea Dulce.
# Uso:       bash scripts/benchmark.sh [ITERACIONES]
# ==============================================================================
set -euo pipefail

ITERATIONS="${1:-25}"

echo "=================================================================="
echo " [Marea Dulce] Ejecutando Benchmark HTTP Sintético (${ITERATIONS} reqs/endpoint)"
echo "=================================================================="

run_bench() {
  local label="$1"
  local path="$2"
  echo ""
  echo "${label} (${path})..."
  kubectl exec -n recreate-lab deploy/marea-app-deployment -- python3 -c "
import urllib.request, time
ok = 0; fail = 0
start = time.time()
for _ in range(${ITERATIONS}):
    try:
        r = urllib.request.urlopen('http://127.0.0.1:8000${path}', timeout=3)
        if r.status == 200:
            ok += 1
        else:
            fail += 1
    except Exception:
        fail += 1
dur = round(time.time() - start, 3)
print(f'  -> Resultado: Total=${ITERATIONS} | HTTP_200={ok} | Errores={fail} | Tiempo={dur}s')
if fail > 0:
    raise SystemExit(1)
"
}

run_bench "[1/4] Benchmark Sondas de Salud" "/healthz"
run_bench "[2/4] Benchmark Catálogo de Productos" "/api/v1/products"
run_bench "[3/4] Benchmark Categorías de Repostería" "/api/v1/categories"
run_bench "[4/4] Benchmark Telemetría y Métricas" "/metrics"

echo ""
echo "=================================================================="
echo " [Marea Dulce] Benchmark Completado Exitosamente (0% Error Rate)."
echo "=================================================================="
