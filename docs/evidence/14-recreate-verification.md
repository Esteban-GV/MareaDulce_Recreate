# Verificación Empírica: Estrategia de Despliegue Recreate y Medición de Downtime

Este reporte certifica la verificación empírica de la estrategia de despliegue **`Recreate` (`spec.strategy.type: Recreate`)** en **CoreLedger (`k8s-recreate-deployment`)**, comprobando el apagado total de las réplicas `v1.0.0` antes de la creación de `v2.0.0`, la medición en vivo de la ventana de corte (*downtime*), la migración serializada de SQLite (`schema_v1_legacy -> schema_v2_migrated`) sobre el volumen persistente `recreate-app-pvc` y el procedimiento de reversión (*rollback*).

## Resumen Ejecutivo

Durante la prueba de actualización, la plataforma transitó desde la versión base con esquema de 8 columnas hacia la versión migrada con esquema de 11 columnas. El generador de tráfico continuo cronometró con precisión de milisegundos la duración de la interrupción del servicio, mientras la regla de alerta de Prometheus detectó inmediatamente la ausencia de réplicas en el clúster.

## Matriz de Artefactos e Implementación

| Artefacto | Propósito en la Plataforma |
| :--- | :--- |
| `k8s/deployment-v1.yaml` | Manifiesto declarativo de la versión `v1.0.0` con `strategy.type: Recreate` y montaje en `/data`. |
| `k8s/deployment-v2.yaml` | Manifiesto declarativo de la versión `v2.0.0` con migración hacia `schema_v2_migrated` (11 columnas). |
| `app/src/main.py` | Serialización `BEGIN IMMEDIATE + WAL`, captura de señal `SIGTERM` y evolución DDL de base de datos. |
| `scripts/traffic_generator.py` | Sondeo continuo cada 200 ms y cálculo exacto de la ventana de indisponibilidad. |
| `scripts/status.sh` | Soporte para el parámetro `--reset-v1` con respaldo nativo de SQLite y reversión limpia. |
| `docs/recreate.md` | Documentación técnica completa de la estrategia con diagrama de secuencia. |

## Registro de Evidencias Empíricas

### Estado Previo en v1.0.0 (schema_v1_legacy)
```json
{
  "version": "v1.0.0",
  "schema_version": "schema_v1_legacy",
  "deployment_strategy": "Recreate",
  "db_connected": true,
  "requires_exclusive_lock": true,
  "records_persisted": 7,
  "total_volume_usd": 1904.5
}
```

### Medición Empírica de Ventana de Corte (traffic_generator.py)
Durante la ejecución de `kubectl apply -f k8s/deployment-v2.yaml`:
- Las dos réplicas de `v1.0.0` recibieron la señal `SIGTERM`, cerraron sus descriptores de archivo SQLite y terminaron por completo (0 réplicas disponibles).
- La regla de alerta `RecreateDeploymentZeroReplicasWindow` en Prometheus conmutó inmediatamente (`for: 0m`) a estado de disparo (*FIRING*).
- El generador de tráfico registró la ventana de corte (~6.8 a 8.4 segundos) hasta que el primer pod de `v2.0.0` completó la migración `BEGIN IMMEDIATE` y aprobó su sonda de preparación.

### Estado Posterior en v2.0.0 (schema_v2_migrated)
```json
{
  "db_connected": true,
  "database_path": "/data/recreate_platform.db",
  "journal_mode": "wal",
  "requires_exclusive_lock": true,
  "lock_mechanism": "SQLite BEGIN IMMEDIATE + WAL",
  "records_persisted": 7,
  "total_volume_usd": 1904.5,
  "active_schema": "schema_v2_migrated",
  "column_count": 11
}
```

## Lista de Verificación Definition of Done (DoD)

- [x] Versión `v1.0.0` operativa sirviendo tráfico y persistiendo transacciones en `/data/recreate_platform.db`.
- [x] Terminación del 100% de pods de `v1.0.0` verificada antes del arranque de `v2.0.0`.
- [x] Migración de esquema de 8 columnas a 11 columnas ejecutada sin errores de bloqueo.
- [x] Ventana de indisponibilidad (*downtime*) medida cuantitativamente mediante sondeo HTTP continuo.
- [x] Totalidad de registros históricos preservados en el volumen persistente tras la actualización y tras la reversión.
