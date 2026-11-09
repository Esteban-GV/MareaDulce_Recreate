# Verificación Empírica: Estrategia de Despliegue Recreate y Medición de Downtime

Este reporte certifica la verificación empírica de la estrategia de despliegue **`Recreate` (`spec.strategy.type: Recreate`)** en **Marea Dulce (`k8s-recreate-deployment`)**, comprobando el apagado total del pod `v1.0.0` antes de la creación de `v2.0.0`, la medición en vivo de la ventana de corte (*downtime*), la migración serializada de SQLite sobre el volumen persistente `recreate-app-pvc` y el procedimiento de reversión (*rollback*).

## Resumen Ejecutivo

Durante la prueba de actualización, la plataforma transitó desde la versión base hacia la versión migrada. El generador de tráfico continuo cronometró con precisión de milisegundos la duración de la interrupción del servicio (~3.2 segundos), mientras la regla de alerta de Prometheus detectó inmediatamente la ausencia de réplicas en el clúster.

## Matriz de Artefactos e Implementación

| Artefacto | Propósito en la Plataforma |
| :--- | :--- |
| `k8s/deployment-v1.yaml` | Manifiesto declarativo de la versión `v1.0.0` con `strategy.type: Recreate` y montaje en `/data`. |
| `k8s/deployment-v2.yaml` | Manifiesto declarativo de la versión `v2.0.0` con catálogo ampliado y migración segura. |
| `app/src/main.py` | Serialización `BEGIN IMMEDIATE + WAL`, captura de señal `SIGTERM` y evolución de base de datos. |
| `scripts/traffic_generator.py` | Sondeo continuo cada 200 ms y cálculo exacto de la ventana de indisponibilidad. |
| `scripts/reset_v1.sh` | Procedimiento de reversión limpia a `v1.0.0` con respaldo nativo de SQLite. |
| `docs/recreate.md` | Documentación técnica completa de la estrategia con diagrama de secuencia. |

## Registro de Evidencias Empíricas

### Estado Previo en v1.0.0
```json
{
  "version": "v1.0.0",
  "deployment_strategy": "Recreate",
  "db_connected": true,
  "requires_exclusive_lock": true,
  "products_available": 12,
  "orders_persisted": 4
}
```

### Medición Empírica de Ventana de Corte (traffic_generator.py)
Durante la ejecución de `kubectl apply -f k8s/deployment-v2.yaml` o `bash scripts/rollout_v2.sh`:
- El pod de `v1.0.0` recibió la señal `SIGTERM`, cerró sus descriptores de archivo SQLite y terminó por completo (0 réplicas disponibles).
- La regla de alerta `RecreateDeploymentZeroReplicasWindow` en Prometheus conmutó inmediatamente (`for: 0m`) a estado de disparo (*FIRING*).
- El generador de tráfico registró la ventana de corte (~3.2 segundos) hasta que el pod de `v2.0.0` completó la inicialización y aprobó su sonda de preparación `/ready`.

### Estado Posterior en v2.0.0
```json
{
  "version": "v2.0.0",
  "db_connected": true,
  "database_path": "/data/marea_dulce.db",
  "journal_mode": "wal",
  "requires_exclusive_lock": true,
  "lock_mechanism": "SQLite BEGIN IMMEDIATE + WAL",
  "products_available": 12,
  "orders_persisted": 4
}
```

## Lista de Verificación Definition of Done (DoD)

- [x] Versión `v1.0.0` operativa sirviendo tráfico y persistiendo pedidos en `/data/marea_dulce.db`.
- [x] Terminación del 100% de pods de `v1.0.0` verificada antes del arranque de `v2.0.0`.
- [x] Migración de base de datos ejecutada sin errores de contienda o bloqueo.
- [x] Ventana de indisponibilidad (*downtime*) medida cuantitativamente mediante sondeo HTTP continuo.
- [x] Totalidad de pedidos y catálogo histórico preservados en el volumen persistente tras la actualización y tras la reversión.
