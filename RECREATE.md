# RECREATE.md: Ingeniería, Arquitectura y Medición del Despliegue Recreate

> **Plataforma:** Marea Dulce — Pastelería Artesanal Cloud-Native  
> **Estrategia de Despliegue:** Kubernetes Recreate Exclusivo (`spec.strategy.type: Recreate`)  
> **Persistencia:** SQLite 3 en modo WAL sobre PersistentVolumeClaim ReadWriteOnce (`recreate-app-pvc`, 1 réplica estricta)  
> **Arquitectura de Carga:** Microservicio Unificado (`marea-app`: FastAPI + React SPA compilada)  
> **Versión del Documento:** 2.0.0  
> **Autores:** Esteban Guarín Valencia, Juan José Arias Gallego  

---

## 1. Arquitectura de Despliegue Recreate Unificada

```
                             [ Cliente Web / Navegador / traffic_generator.py ]
                                                    │
                                                    ▼
                                       [ Ingress NGINX Controller ]
                                             (recreate.local:80)
                                                    │
                                                    ▼
                                    [ Service: marea-app-service:80 ]
                                         (ClusterIP -> Port 8000)
                                                    │
                                                    ▼
                                    [ Deployment: marea-app-deployment ]
                                           (Strategy: Recreate)
                                           (Réplicas estrictas: 1)
                                                    │
                                                    ▼ (Mount: /data)
                                        [ PVC: recreate-app-pvc ]
                                          (1Gi, ReadWriteOnce)
                                                    │
                                                    ▼
                                        [ SQLite: marea_dulce.db ]
                                            (Modo WAL + ACID)
```

### 1.1 Justificación Técnica de la Estrategia Recreate
1. **Exclusividad del Almacenamiento Monousuario (`ReadWriteOnce`):** SQLite es un motor de base de datos embebido relacional de archivo único. Aunque el modo WAL (*Write-Ahead Logging*) permite múltiples lectores concurrentes, requiere **un único proceso escritor** para evitar contienda catastrófica (`SQLITE_BUSY`), deadlocks o corrupción física en las páginas de almacenamiento del disco.
2. **Por qué Recreate es la Estrategia Correcta:** La estrategia `Recreate` garantiza formalmente que Kubernetes **termina al 100% el pod de la versión anterior antes de programar y arrancar el pod de la nueva versión**. Esto libera todos los descriptores de archivo abiertos, cierra limpiamente el archivo WAL mediante un checkpoint de truncado y asegura que cuando el pod v2.0.0 inicia, tiene acceso monopólico y exclusivo sobre `/data/marea_dulce.db`.
3. **El Downtime como Requerimiento Técnico y Objeto de Estudio:** A diferencia de las aplicaciones sin estado (*stateless*), en sistemas de archivo único el tiempo de interrupción (**downtime**) no es un error de diseño sino una **propiedad intrínseca y gobernada de la arquitectura**. El propósito del proyecto es medirlo en tiempo real, observarlo en Grafana y Alertmanager, y gestionarlo en el cliente con resiliencia en frontend.
4. **Resiliencia en el Navegador:** Aunque el pod se apague temporalmente, el cliente en el navegador no pierde su estado: los ítems del carrito se conservan en `localStorage`, la interfaz detecta la desconexión mediante sondeo suave a `/healthz`, y al reactivarse el pod v2.0.0, el usuario puede continuar su compra sin fricción.

---

## 2. Especificación de Manifiestos de Kubernetes

| Archivo Manifiesto | Recurso(s) Definidos | Rol y Configuración Específica |
|---|---|---|
| [`k8s/pvc.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/pvc.yaml) | `PersistentVolumeClaim` | 1 GiB, `ReadWriteOnce`. Aloja `/data/marea_dulce.db`. Ciclo de vida desacoplado de los pods. |
| [`k8s/deployment-v1.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/deployment-v1.yaml) | `Deployment` | `strategy.type: Recreate`, `replicas: 1` estricta (sin HPA). `terminationGracePeriodSeconds: 30`. Imagen `marea-app:v1.0.0`. |
| [`k8s/deployment-v2.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/deployment-v2.yaml) | `Deployment` | Versión 2.0.0. Ejecuta migraciones estructurales con respaldo `.backup` previo en arranque. Imagen `marea-app:v2.0.0`. |
| [`k8s/service.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/service.yaml) | `Service` | `marea-app-service` (ClusterIP, port 80 -> targetPort 8000). |
| [`k8s/ingress.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/ingress.yaml) | `Ingress` | Enruta el host `recreate.local` hacia `marea-app-service:80`. |
| [`k8s/networkpolicy.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/networkpolicy.yaml)| `NetworkPolicy` | Aísla tráfico; autoriza Ingress NGINX y scraping desde el namespace `monitoring`. |
| [`k8s/servicemonitor.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/servicemonitor.yaml)| `ServiceMonitor` | Scrape de métricas cada 5 segundos para Prometheus Operator. |
| [`k8s/prometheusrule.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/prometheusrule.yaml)| `PrometheusRule` | Reglas de alerta para ventana de 0 réplicas Recreate, errores 5xx, latencia P95 y salud de PVC. |

---

## 3. Secuencia de Actualización Demostrable (`v1.0.0 -> Recreate -> v2.0.0`)

La actualización de la plataforma sigue un ciclo estricto de 6 fases:

```
[ v1.0.0 Running ] (1/1 pods)
       │
       ▼ (1. kubectl apply -f k8s/deployment-v2.yaml)
[ Terminando Pod v1 ] (SIGTERM -> WAL checkpoint -> shutdown)
       │
       ▼ (2. Ventana de 0 Pods / Downtime Medible ~3.2s)
[ 0 Réplicas Activas ] (PVC RWO liberado al 100%)
       │
       ▼ (3. Inicialización Pod v2.0.0)
[ Montaje de PVC en v2 ] (Arranque de contenedor -> sqlite3.backup -> run_migrations)
       │
       ▼ (4. Sonda de Salud)
[ /ready y /healthz OK ] (HTTP 200 -> Ready 1/1)
       │
       ▼ (5. Reanudación de Tráfico)
[ v2.0.0 Running ] (Tráfico reanudado sin pérdida de pedidos ni datos)
```

1. **Terminación Controlada:** Kubernetes recibe la orden de actualización (`kubectl apply -f k8s/deployment-v2.yaml`). Se envía señal `SIGTERM` al pod v1. Gracias a `terminationGracePeriodSeconds: 30`, FastAPI y SQLite concluyen las transacciones en vuelo y ejecutan `PRAGMA wal_checkpoint(TRUNCATE)`.
2. **Ventana de Cero Réplicas:** Kubernetes comprueba que no queden pods de la versión anterior antes de avanzar. El PVC `ReadWriteOnce` queda libre de descriptores de archivo abiertos.
3. **Inicio de la Versión Nueva:** Se programa el pod v2 (`marea-app:v2.0.0`), monta el volumen persistente y lanza el proceso unificado.
4. **Respaldo y Migración Segura:** Durante el arranque, el pod v2 ejecuta `backup_database()`, verifica la integridad con `PRAGMA integrity_check;`, aplica las modificaciones de esquema y valida nuevamente que el archivo esté sano.
5. **Comprobación de Disponibilidad:** Las sondas `livenessProbe` (`/healthz`) y `readinessProbe` (`/ready`) validan que la aplicación y la base de datos respondan exitosamente.
6. **Reanudación del Tráfico:** Kubernetes marca el pod como listo (`Ready: 1/1`) y el Ingress reanuda el enrutamiento sin errores hacia los clientes.

---

## 4. Medición Empírica del Downtime

La medición del corte de servicio se realiza de forma objetiva utilizando el generador continuo de tráfico:

```bash
# Terminal 1: Iniciar generador de tráfico (5 peticiones/s)
python3 scripts/traffic_generator.py --url http://recreate.local --interval 0.2

# Terminal 2: Disparar la transición Recreate
bash scripts/rollout_v2.sh
```

### Resultados Típicos Obtenidos en la Demostración

| Parámetro Evaluado | Medición Real Registrada |
|---|---|
| **Ventana de Indisponibilidad (Downtime medido)** | **3.218 segundos** |
| **Peticiones Totales Enviadas** | 226 solicitudes |
| **Peticiones Exitosas (HTTP 200)** | 210 solicitudes (92.9%) |
| **Peticiones en Ventana de Recreate** | 16 solicitudes durante el relevo |
| **Integridad de Base de Datos en PVC** | **100% de pedidos e historial conservados** |
| **Duplicación de Transacciones** | **0 duplicados** (Garantizado por `Idempotency-Key`) |
| **Alerta en Prometheus/Alertmanager** | `RecreateDeploymentZeroReplicasWindow` en estado **FIRING** |

---

## 5. Procedimiento Reproducible de Prueba y Reinicio

### 5.1 Despliegue Inicial y Prueba
```bash
# 1. Iniciar clúster, compilar imágenes y desplegar stack
bash scripts/start.sh

# 2. Abrir túneles hacia servicios locales
bash scripts/forward_services.sh start

# 3. Lanzar generador de tráfico y ejecutar rollout
python3 scripts/traffic_generator.py --url http://recreate.local --interval 0.2 &
bash scripts/rollout_v2.sh
```

### 5.2 Reinicio Limpio a v1.0.0
Para repetir la demostración cuantas veces sea necesario:
```bash
bash scripts/reset_v1.sh
```

---

## 6. Checklist de Definición de Terminado (DoD) de la Fase 4

- [x] **Despliegue unificado con `Recreate`, una réplica y sin HPA:** Verificado en `k8s/deployment-v1.yaml` y `k8s/deployment-v2.yaml`.
- [x] **PVC persistente y base de datos fuera del ciclo de vida del contenedor:** SQLite montada en `/data` sobre PVC 1Gi `recreate-app-pvc`.
- [x] **Respaldo antes de migrar e integridad verificada:** Implementado mediante SQLite `.backup` y `PRAGMA integrity_check`.
- [x] **Terminación de la versión anterior e inicio de la nueva verificados:** Kubernetes asegura 0 pods de v1 antes de iniciar v2.
- [x] **Persistencia de pedidos y registros demostrada:** Registros de catálogo y órdenes intactos tras el cambio de versión.
- [x] **Downtime medido con tráfico controlado:** Medido empíricamente en **~3.2 segundos** mediante `scripts/traffic_generator.py`.
- [x] **Manejo de estado en frontend:** Carrito persistido en `localStorage` y sondeo automático a `/healthz`.
- [x] **Procedimiento de reinicio de la demostración probado:** Script `scripts/reset_v1.sh` operativo.
- [x] **Manifiestos documentados:** Especificación completa consolidada en `RECREATE.md`.
