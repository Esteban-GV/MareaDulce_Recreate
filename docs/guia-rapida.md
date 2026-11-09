# Guía Rápida: Instalación, Demostración Recreate y Reversión a v1

**Plataforma:** Marea Dulce — E-Commerce Cloud-Native sobre Kubernetes  
**Estrategia:** `Recreate` (`spec.strategy.type: Recreate`, `replicas: 1`)  
**Almacenamiento:** SQLite en modo WAL sobre PVC ReadWriteOnce (1 GiB)  

---

## 1. Requisitos del Sistema

| Componente | Requisito Recomendado | Detalle |
|---|---|---|
| **Sistema Operativo** | Linux (o Docker Desktop) | Entorno nativo con soporte cgroups v2. |
| **Procesador (CPU)** | 6 a 8 hilos | 6 CPUs asignadas a Minikube. |
| **Memoria RAM** | 16 GiB | 10 GiB asignados a Minikube (para app, Prometheus, ELK). |
| **Herramientas Host** | Instaladas en `$PATH` | `docker`, `minikube`, `kubectl`, `helm`, `python3`. |

---

## 2. Puesta en Marcha Rápida (2 Pasos)

Toda la inicialización está completamente automatizada e incluye auto-activación de grupo Docker (`newgrp docker`), verificación de herramientas, arranque idempotente de Minikube con addons, compilación de imágenes OCI y despliegue de observabilidad:

### Paso 1: Iniciar la plataforma completa
```bash
bash scripts/start.sh
```

### Paso 2: Abrir los túneles locales de red
```bash
bash scripts/forward_services.sh start
```

---

## 3. URLs y Servicios Disponibles

Una vez iniciados los túneles, todos los servicios quedan accesibles localmente:

| Servicio / Interfaz | URL Local | Credenciales | Propósito |
|---|---|---|---|
| **Tienda Web Marea Dulce** | `http://localhost:8000/` | Libre | Storefront SPA, catálogo, carrito, personalizador de pasteles y checkout. |
| **API REST / Swagger Docs** | `http://localhost:8000/docs` | Libre | Documentación OpenAPI interactiva de todos los endpoints. |
| **Métricas Prometheus** | `http://localhost:8000/metrics` | Libre | Telemetría OpenMetrics (RED, USE, pedidos, ingresos COP y SQLite). |
| **Tablero Grafana** | `http://localhost:3000` | `admin` / `admin123` | Dashboard oficial `marea-dulce-recreate` con medición de corte en tiempo real. |
| **Prometheus UI** | `http://localhost:9090` | Libre | Explorador de métricas PromQL y estado de alertas. |
| **Alertmanager** | `http://localhost:9093` | Libre | Consola de alertas activas (`FIRING` / `PENDING`). |
| **Kibana (Pila ELK)** | `http://localhost:5601` | Libre | Visualización de logs centralizados, trazas de parada SIGTERM y migraciones. |

---

## 4. Diagnóstico y Validación Automatizada

Para verificar la salud integral del clúster antes o después de una prueba:

```bash
# Ver estado consolidado (pods, PVC, réplicas, observabilidad)
bash scripts/status.sh

# Ejecutar la suite automatizada de 16 pruebas E2E
bash scripts/validate.sh

# Ejecutar prueba sintética de latencia y rendimiento HTTP
bash scripts/benchmark.sh
```

---

## 5. Guía para Probar la Transición Recreate (v1.0.0 $\rightarrow$ v2.0.0)

El objetivo de esta prueba es **demostrar empíricamente cómo opera la estrategia Recreate** en Kubernetes ante un motor de base de datos de archivo único (SQLite) sobre almacenamiento exclusivo `ReadWriteOnce`:

```
[ Pod v1.0.0 ] ──(SIGTERM / Checkpoint WAL)──> [ 0 Pods: Ventana de Corte ~3.2s ] ──> [ Pod v2.0.0 Listo ]
                                                        │
                                                        ▼
                                       (Medición con traffic_generator.py)
```

### Paso 1: Generar datos iniciales en la tienda (v1.0.0)
1. Abra `http://localhost:8000/` en su navegador.
2. Agregue una **Torta Marea de Chocolate** al carrito.
3. Vaya al checkout y complete el pedido para que quede registrado en el archivo `/data/marea_dulce.db` del PVC.

### Paso 2: Iniciar el medidor continuo de tráfico (Terminal 1)
En una terminal, lance el generador de tráfico para cronometrar la interrupción:
```bash
python3 scripts/traffic_generator.py --url http://recreate.local --interval 0.2
```

### Paso 3: Disparar la actualización Recreate (Terminal 2)
En otra terminal, aplique el despliegue de la versión 2.0.0:
```bash
bash scripts/rollout_v2.sh
```

### Paso 4: Qué observar durante la demostración
1. **En la Terminal:** Kubernetes finaliza completamente el pod v1 (`terminationGracePeriodSeconds: 30` permite vaciar transacciones y cerrar WAL). Durante unos segundos no hay pods activos (**0 réplicas**). Luego se crea el pod v2, monta el PVC y ejecuta las migraciones de esquema.
2. **En el Generador de Tráfico:** Verá cómo las peticiones fallan brevemente y el script cronometra con exactitud milimétrica el tiempo de interrupción:
   ```text
   ======================================================================
   RESUMEN DE TELEMETRÍA Y OBSERVABILIDAD
   Tiempo total evaluado: 42.10 segundos
   Total de solicitudes enviadas: 210
   Solicitudes exitosas: 194 (92.4%)
   Solicitudes fallidas: 16 (7.6%)
   Ventana de indisponibilidad (Downtime medido): 3.218 segundos
   Integridad de base de datos: 100% registros persistidos en PVC
   ======================================================================
   ```
3. **En el Navegador (Frontend SPA):** La tienda muestra el aviso de mantenimiento suave (*"Estamos actualizando la tienda. Tu carrito está guardado"*), el carrito no se pierde gracias a `localStorage`, y al volver el pod v2, la página reanuda la conexión automáticamente.
4. **En Grafana (`http://localhost:3000`):**
   - El panel **"Réplicas Disponibles"** cae a 0.
   - El panel **"Estado de Ventana de Interrupción"** se ilumina en rojo durante el corte.
   - Las curvas de latencia y errores HTTP del Ingress capturan el intervalo exacto.
   - Los pedidos acumulados y ventas en Pesos Colombianos (COP) permanecen intactos.

---

## 6. Guía para Revertir a la Versión 1.0.0 (Repetir Demostración)

Para volver a comenzar la prueba cuantas veces sea necesario (por ejemplo, para ensayar la sustentación o presentarla al jurado):

### Opción A: Reversión Rápida
```bash
bash scripts/reset_v1.sh
```
Aplica `k8s/deployment-v1.yaml` y espera a que el pod v1 esté en estado `Ready`.

### Opción B: Reversión con Respaldo Automático de Base de Datos
```bash
bash scripts/status.sh --reset-v1
```
Este comando ejecuta una copia de seguridad en caliente mediante la API SQLite `.backup` en `/data/backups/`, comprueba la integridad (`PRAGMA integrity_check`) y luego restablece el despliegue a la versión 1.0.0.

---

## 7. Disparo de Alarmas de Prueba (Prometheus y Alertmanager)

Para evidenciar ante el jurado cómo Alertmanager detecta anomalías operativas:

```bash
# Disparar 50 errores HTTP 500 para activar alerta HighHttp5xxErrorRate
python3 scripts/test_alerts.py --url http://recreate.local --type errors --errors-count 50

# Disparar solicitudes lentas para activar alerta HighRequestLatencyP95
python3 scripts/test_alerts.py --url http://recreate.local --type latency --latency-count 10 --latency-delay 1.5
```
Compruebe en `http://localhost:9093` (Alertmanager) y en `http://localhost:3000` (Grafana) cómo las alertas transicionan de `Inactive` a `FIRING`.

---

## 8. Parada y Limpieza de la Plataforma

Al finalizar la sesión de trabajo o la demostración:

```bash
# Detiene los túneles de red y apaga Minikube (conservando los datos del PVC en disco)
bash scripts/stop.sh
```
Si desea únicamente detener las réplicas sin apagar el clúster:
```bash
bash scripts/stop.sh --scale-zero
```
