# Plan y Matriz de Pruebas de Calidad (QA) — Marea Dulce

**Proyecto:** Marea Dulce — Plataforma E-Commerce Cloud-Native sobre Kubernetes  
**Estrategia Evaluada:** `Recreate` (`spec.strategy.type: Recreate`, `replicas: 1`)  
**Autores:** Esteban Guarín Valencia, Juan José Arias Gallego  
**Versión de Documento:** 1.0.0

---

## 1. Alcance y Objetivos de Calidad

Este documento define la estrategia integral de aseguramiento de calidad (QA) para la plataforma Marea Dulce. Dado que el objetivo académico y técnico es demostrar el comportamiento, beneficios, limitaciones y observabilidad de la estrategia **Recreate** en Kubernetes, las pruebas cubren tanto los requerimientos funcionales del e-commerce artesanal como las restricciones no funcionales de infraestructura:

1. **Garantía de Persistencia:** Ningún pedido ni dato relacional de clientes puede perderse o corromperse al destruirse el pod v1.0.0 y crearse el pod v2.0.0.
2. **Medición del Ciclo Recreate:** Verificación determinista de la ventana de corte (downtime medido en segundos) mediante generador continuo de tráfico.
3. **Idempotencia y Concurrencia:** Protección contra pedidos duplicados (`Idempotency-Key`) y control de bloqueos de base de datos (`BEGIN IMMEDIATE`).
4. **Resiliencia en el Frontend:** Comprobación de que la SPA de React gestiona el periodo de corte sin perder el carrito y mostrando mensajes claros al cliente.
5. **Telemetría y Alertas:** Validación de que las métricas RED/USE y las reglas de Prometheus se activan durante el ciclo de vida del contenedor.

---

## 2. Matriz Consolidada de Pruebas

| ID | Capa | Prueba | Tipo | Criterio de Éxito | Estado |
|---|---|---|---|---|---|
| **QA-01** | Backend | Sondas Kubernetes (`/healthz`, `/ready`) | Automatizada | Ambos endpoints responden HTTP 200 con payload de estado. | **PASS** |
| **QA-02** | Backend | Exposición OpenMetrics (`/metrics`) | Automatizada | Formato estándar Prometheus con métricas RED y de negocio. | **PASS** |
| **QA-03** | Backend | Catálogo de Semilla Inicial | Automatizada | 6 categorías y 12 productos artesanales cargados en SQLite. | **PASS** |
| **QA-04** | Backend | Autenticación y RBAC (JWT + Bcrypt) | Automatizada | Acceso restringido con credenciales válidas y protección de rutas admin. | **PASS** |
| **QA-05** | Backend | Creación Atómica de Pedidos | Automatizada | Deducción de stock en SQLite y deduplicación con `Idempotency-Key`. | **PASS** |
| **QA-06** | Backend | Máquina de Estados de Pedidos | Automatizada | Transiciones válidas y bloqueo de cancelaciones inválidas. | **PASS** |
| **QA-07** | Backend | Control de Stock Insuficiente | Automatizada | Respuesta HTTP 400 con mensaje descriptivo y reversión atómica. | **PASS** |
| **QA-08** | Backend | Respaldo y Verificación de Integridad | Automatizada | API `.backup` crea copia funcional con `PRAGMA integrity_check = ok`. | **PASS** |
| **QA-09** | Frontend | Compilación TypeScript y Bundling Vite | Automatizada | Cero errores de tipado (`tsc -b`), bundle optimizado en `frontend/dist/`. | **PASS** |
| **QA-10** | Frontend | Persistencia Local del Carrito | E2E / Funcional | Carrito guardado en `localStorage` sobrevive a desconexión y refresco. | **PASS** |
| **QA-11** | Frontend | Banner de Mantenimiento Recreate | E2E / Visual | Al recibir error de conexión, se muestra aviso amigable sin borrar datos. | **PASS** |
| **QA-12** | K8s | Declaración Estricta `strategy.type: Recreate` | Infraestructura | Manifiesto `k8s/deployment-v1.yaml` y v2 con `Recreate` y `replicas: 1`. | **PASS** |
| **QA-13** | K8s | Almacenamiento PVC ReadWriteOnce | Infraestructura | `recreate-app-pvc` montado en `/data` con enlace exitoso (`Bound`). | **PASS** |
| **QA-14** | K8s | Aislamiento NetworkPolicy | Infraestructura | Tráfico restringido al Ingress NGINX y al namespace `monitoring`. | **PASS** |
| **QA-15** | Observabilidad | Detección de Ventana de 0 Réplicas | Telemetría | Alerta `RecreateDeploymentZeroReplicasWindow` se activa durante el corte. | **PASS** |
| **QA-16** | Observabilidad | Tablero Grafana Marea Dulce | Visualización | 10 paneles activos con consultas PromQL válidas para RED, USE y FinOps. | **PASS** |
| **QA-17** | E2E | Medición de Downtime con Tráfico Activo | Automatizada | `traffic_generator.py` captura 100% de la ventana de indisponibilidad. | **PASS** |
| **QA-18** | E2E | Validación Integral del Clúster (`validate.sh`) | Automatizada | 16/16 verificaciones superadas exitosamente en tiempo real. | **PASS** |

---

## 3. Ejecución de Pruebas Automatizadas

### 3.1 Suite de Pruebas Unitarias e Integración (Pytest)
Para ejecutar la batería completa de pruebas del backend sobre SQLite en memoria y disco local:
```bash
PYTHONPATH=app ./.venv/bin/pytest app/tests/test_backend.py -v
```
**Resultado esperado:**
```
app/tests/test_backend.py::test_health_and_probes PASSED                 [ 12%]
app/tests/test_backend.py::test_metrics_endpoint PASSED                  [ 25%]
app/tests/test_backend.py::test_catalog_seeded_data PASSED               [ 37%]
app/tests/test_backend.py::test_auth_and_roles PASSED                    [ 50%]
app/tests/test_backend.py::test_order_creation_stock_deduction_and_idempotency PASSED [ 62%]
app/tests/test_backend.py::test_order_status_transitions_and_cancellation PASSED [ 75%]
app/tests/test_backend.py::test_insufficient_stock_error PASSED          [ 87%]
app/tests/test_backend.py::test_database_backup_and_integrity PASSED     [100%]

========================= 8 passed in 1.98s =========================
```

### 3.2 Compilación y Verificación de Tipos del Frontend
```bash
cd frontend
npm run build
```
**Resultado esperado:**
```
vite v5.4.14 building for production...
transforming...
✓ 184 modules transformed.
dist/index.html                   1.12 kB │ gzip:  0.48 kB
dist/assets/index-Dk_2oFz0.css   21.45 kB │ gzip:  4.68 kB
dist/assets/index-B7jP47N8.js   198.32 kB │ gzip: 62.11 kB
✓ built in 2.22s
```

### 3.3 Suite Automatizada End-to-End (`validate.sh`)
Verifica todos los componentes desplegados en el clúster de Kubernetes:
```bash
bash scripts/validate.sh
```
**Resultado esperado:**
```
==============================================================================
 SUITE DE VALIDACIÓN AUTOMATIZADA — MAREA DULCE (K8S RECREATE STACK)
==============================================================================
[PASS] 01. Clúster de Kubernetes accesible vía kubectl
[PASS] 02. Namespace 'recreate-lab' existente y activo
[PASS] 03. Deployment 'marea-app-deployment' configurado con estrategia exclusiva 'Recreate'
[PASS] 04. Réplicas de 'marea-app-deployment' en estado Running/Ready (1 activas)
[PASS] 05. PersistentVolumeClaim 'recreate-app-pvc' enlazado (Bound, ReadWriteOnce)
[PASS] 06. Política de red 'marea-dulce-network-policy' activa
[PASS] 07. Service 'marea-app-service' e Ingress 'marea-app-ingress' configurados
[PASS] 08. CRDs de Observabilidad (marea-app-servicemonitor y marea-app-alert-rules) registrados
[PASS] 09. Sondas Liveness (/healthz) y Readiness (/ready) responden HTTP 200
[PASS] 10. Storefront SPA de Marea Dulce servido correctamente en '/'
[PASS] 11. Endpoint de versión responde con versión semántica activa (1.0.0)
[PASS] 12. Catálogo poblado en SQLite: 6 categorías, 12 productos artesanales
[PASS] 13. Creación atómica de pedido con deducción de stock e Idempotency-Key
[PASS] 14. Autenticación administrativa y métricas operativas de pedidos validadas
[PASS] 15. Endpoint '/metrics' expone telemetría RED y métricas de negocio (marea_orders_total)
[PASS] 16. Stack de Observabilidad (Prometheus, Grafana, Alertmanager) en estado Running
==============================================================================
 RESUMEN DE VALIDACIÓN: 16 EXITOSAS (PASS) | 0 FALLIDAS (FAIL)
==============================================================================
```

### 3.4 Benchmark Sintético de Rendimiento (`benchmark.sh`)
```bash
bash scripts/benchmark.sh 25
```
**Resultado esperado:**
```
==================================================================
 [Marea Dulce] Ejecutando Benchmark HTTP Sintético (25 reqs/endpoint)
==================================================================
[1/4] Benchmark Sondas de Salud (/healthz)...
  -> Resultado: Total=25 | HTTP_200=25 | Errores=0 | Tiempo=0.142s

[2/4] Benchmark Catálogo de Productos (/api/v1/products)...
  -> Resultado: Total=25 | HTTP_200=25 | Errores=0 | Tiempo=0.188s

[3/4] Benchmark Categorías de Repostería (/api/v1/categories)...
  -> Resultado: Total=25 | HTTP_200=25 | Errores=0 | Tiempo=0.135s

[4/4] Benchmark Telemetría y Métricas (/metrics)...
  -> Resultado: Total=25 | HTTP_200=25 | Errores=0 | Tiempo=0.152s

==================================================================
 [Marea Dulce] Benchmark Completado Exitosamente (0% Error Rate).
==================================================================
```

---

## 4. Procedimiento de Prueba de Aceptación ante Jurado (Demo Script)

1. **Estado Inicial:** Ejecutar `./scripts/status.sh` y mostrar que el pod `marea-app-deployment` está en versión `1.0.0` y el tablero de Grafana refleja 1 réplica activa.
2. **Navegación Comercial:** Abrir `http://localhost:8000/` o `http://recreate.local`, agregar una Torta Marea de Chocolate y un Cheesecake de Frutos Rojos al carrito, y completar el pedido en checkout.
3. **Inicio del Medidor de Downtime:**
   ```bash
   python3 scripts/traffic_generator.py --url http://recreate.local --interval 0.2
   ```
4. **Disparo del Rollout Recreate a v2.0.0:**
   ```bash
   bash scripts/rollout_v2.sh
   ```
5. **Observación en Vivo:**
   - La terminal muestra la terminación de `v1.0.0` y la ventana de 0 pods.
   - En el navegador, el banner de mantenimiento suave informa al usuario que la tienda se está actualizando y que su carrito está protegido.
   - Tan pronto el pod `v2.0.0` pasa la sonda `/ready`, el generador de tráfico reporta la reanudación y calcula el downtime exacto (~3.2 s).
6. **Verificación de Persistencia y Migración:**
   - El catálogo muestra la versión `2.0.0`.
   - En el panel de administración (`/admin`), el pedido realizado previamente en `v1.0.0` permanece intacto con su detalle y monto en COP.
   - El archivo de respaldo previo a la migración se encuentra guardado en `/data/backups/`.
7. **Disparo de Alertas de Demostración:**
   ```bash
   python3 scripts/test_alerts.py --type all
   ```
   - Mostrar en Prometheus Alertmanager (`http://localhost:9093`) y en Grafana (`http://localhost:3000`) cómo la alerta `HighHttp5xxErrorRate` y `HighRequestLatencyP95` transicionan a `FIRING`.
