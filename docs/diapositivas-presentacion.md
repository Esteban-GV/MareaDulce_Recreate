# Estructura y Contenido de las Diapositivas de Presentación

---

## Propuestas de Nombres para el Proyecto

1. **KubeRecreate: Plataforma Resiliente y Observabilidad Integral de Despliegues en Kubernetes**
2. **K8s Recreate Observability Suite: Análisis de Ciclo de Vida, Downtime y FinOps**
3. **Telemetría y Control Operativo en Estrategias de Despliegue No Concurrentes**
4. **Arquitectura de Despliegue Recreate y Pila de Observabilidad RED/USE en Kubernetes**

---

## Formato y Convención de Diseño de las Diapositivas

- **Fondo sugerido:** Oscuro formal (`#0f172a` Slate Dark) con acentos en azul cian (`#38bdf8`) para infraestructura y verde esmeralda (`#34d399`) para métricas de éxito.
- **Tipografía recomendada:** Sans-serif moderna (Inter o Roboto) para títulos y texto; fuente monoespaciada (JetBrains Mono o Fira Code) para comandos y métricas.
- **Estructura visual:** Sin párrafos extensos; bloques compactos con viñetas concisas, comandos destacados y recuadros designados para reproducción de video o demostración en vivo.

---

## Slide 1 | Portada y Contexto Ejecutivo

```text
+---------------------------------------------------------------------------------------+
|  [SUBTÍTULO / CÁTEDRA] Plataformas II - Entrega de Arquitectura e Infraestructura    |
|                                                                                       |
|  KubeRecreate: Plataforma Resiliente y Observabilidad Integral                        |
|  Estrategia Recreate, Telemetría RED/USE, FinOps y Seguridad en Kubernetes            |
|                                                                                       |
|  Expositores:                                                                         |
|  - Esteban Guarín Valencia (Ingeniero de Plataformas)                                 |
|  - Juan José Arias Gallego (Ingeniero de Plataformas)                                 |
|                                                                                       |
|  [ESTADO DEL CLÚSTER] Minikube Local | 4 vCPUs | 8 GB RAM | Docker Driver              |
+---------------------------------------------------------------------------------------+
```

---

## Slide 2 | Justificación de Arquitectura: Estrategia Recreate

```text
+---------------------------------------------------------------------------------------+
|  DECISIÓN DE ARQUITECTURA: ROLLINGUPDATE VS. RECREATE                                 |
+---------------------------------------------------+-----------------------------------+
|  Comparativa de Disponibilidad y Consistencia     |  Casos de Uso Obligatorios        |
|  - RollingUpdate: Alta disponibilidad continua,   |  1. Ruptura de Esquema en BD:     |
|    pero conviven versiones v1 y v2 simultáneas.   |     Migraciones destructivas.     |
|  - Recreate: Interrupción planificada (downtime), |  2. Almacenamiento RWO (PVC):     |
|    pero garantiza aislamiento total de versión.   |     Bloqueo físico de volumen.    |
|                                                   |  3. Mensajería / Procesamiento:   |
|  Criterio de Decisión Técnica:                    |     Prevención de doble consumo.  |
|  "Priorizar la consistencia estricta de datos     |                                   |
|   mediante una ventana de corte controlada".      |                                   |
+---------------------------------------------------+-----------------------------------+
|  [ESPACIO VISUAL / DIAGRAMA]                                                          |
|  Flujo: Pods v1 (Terminando) -> 0 Pods (Downtime) -> Pods v2 (Arranque Limpio)        |
+---------------------------------------------------------------------------------------+
```

---

## Slide 3 | Arquitectura Global de la Plataforma

```text
+---------------------------------------------------------------------------------------+
|  MAPA DE COMPONENTES DEL CLÚSTER                                                      |
+---------------------------------------------------+-----------------------------------+
|  Capa de Cargas de Trabajo (Namespace: recreate-lab)|  Pila de Observabilidad y Soporte |
|  - Ingress Controller (recreate.local)            |  - Prometheus Operator            |
|  - Service (ClusterIP en puerto 80)               |  - Grafana (Dashboards RED/USE)   |
|  - Deployment (spec.strategy.type: Recreate)      |  - Kubecost (Monitoreo FinOps)    |
|  - PersistentVolumeClaim (1 GiB RWO en /data)     |  - Pila ELK (Logs en tiempo real) |
|  - NetworkPolicy (Aislamiento Ingress/Egress)     |  - Metrics Server + HPA           |
+---------------------------------------------------+-----------------------------------+
|  Puntos Clave Implementados:                                                          |
|  - Control estricto de red: solo Ingress y Prometheus tienen acceso al Pod.          |
|  - Sondas obligatorias: livenessProbe (/healthz) y readinessProbe (/ready).           |
+---------------------------------------------------------------------------------------+
```

---

## Slide 4 | Régimen Nominal (Versión 1.0.0 Activa)

```text
+---------------------------------------------------------------------------------------+
|  ESTADO DE OPERACIÓN NOMINAL: VERSIÓN 1.0.0                                          |
+---------------------------------------------------+-----------------------------------+
|  Línea Base de Telemetría                         |  [VIDEO DEMO 1 / LIVE DEMO]       |
|  - Réplicas en ejecución: 2/2 Pods en Running     |  Duración: 20-30 segundos         |
|  - Tráfico HTTP: Tasa estable (10 req/s)          |                                   |
|  - Tasa de Error: 0.00%                           |  Contenido del Video:             |
|  - Latencia promedio: < 15 ms                     |  1. Navegador cargando la web     |
|  - Almacenamiento: Contador en PVC funcionando   |     en azul (Versión v1.0.0).     |
|                                                   |  2. Contador en /data subiendo.   |
|  Comandos de Comprobación:                        |  3. Panel de Grafana mostrando    |
|  $ kubectl get pods -n recreate-lab               |     línea verde de 200 OK y       |
|  $ curl http://recreate.local/api/info            |     cero errores 5xx.             |
+---------------------------------------------------+-----------------------------------+
```

---

## Slide 5 | Demostración Central: Actualización Recreate y Medición de Downtime

```text
+---------------------------------------------------------------------------------------+
|  CICLO DE DESPLIEGUE RECREATE: EL MOMENTO DEL DOWNTIME                                |
+---------------------------------------------------+-----------------------------------+
|  Comando de Actualización:                        |  [VIDEO DEMO 2 / LIVE DEMO]       |
|  $ kubectl apply -f k8s/deployment-v2.yaml        |  Duración: 30-40 segundos         |
|                                                   |                                   |
|  Monitoreo en Vivo:                               |  Contenido del Video:             |
|  $ python3 scripts/traffic_generator.py           |  Pantalla dividida (Split screen):|
|                                                   |  - Izquierda: Terminal ejecutando |
|  Fenómeno Observado:                              |    traffic_generator.py viendo    |
|  1. Pods v1 reciben SIGTERM simultáneo.           |    la transición 200 -> 503 -> 200|
|  2. Ventana de 0 Pods activos -> Fallos 503.      |  - Derecha: Lens / kubectl con los|
|  3. Pods v2 inicializan y superan readinessProbe. |    Pods v1 muriendo y v2 naciendo |
|                                                   |  - Resultado: Resumen final de    |
|  Telemetría Obtenida:                             |    downtime en segundos.          |
|  - Downtime exacto registrado: ~6.5 segundos      |                                   |
|  - Pérdida transaccional cuantificada.            |                                   |
+---------------------------------------------------+-----------------------------------+
```

---

## Slide 6 | Verificación Post-Corte: Versión 2.0 y Persistencia de Datos

```text
+---------------------------------------------------------------------------------------+
|  VALIDACIÓN DE INTEGRIDAD POST-DESPLIEGUE                                             |
+---------------------------------------------------+-----------------------------------+
|  Resultados Confirmados:                           |  [VIDEO DEMO 3 / SCREENSHOT]      |
|  - Nueva Versión Activa: v2.0.0 (Interfaz verde)  |  Duración: 15-20 segundos         |
|  - Tráfico 100% restablecido en réplicas v2.      |                                   |
|  - Tasa de errores vuelve a 0.00%.                |  Contenido del Video:             |
|                                                   |  1. Refresco del navegador web:   |
|  Comprobación Crítica de Persistencia (PVC):      |     cambio visual a verde.        |
|  - El archivo /data/counter.txt conservó el valor |  2. Inspección del valor del      |
|    acumulado por los Pods anteriores.             |     contador persistido:          |
|  - Demostración de que Recreate no destruye datos |     $ kubectl exec -it <pod_v2>   |
|    al reciclar los contenedores.                  |       -- cat /data/counter.txt    |
+---------------------------------------------------+-----------------------------------+
```

---

## Slide 7 | Prueba de Carga y Autoescalado Horizontal (HPA)

```text
+---------------------------------------------------------------------------------------+
|  ELASTICIDAD Y COMPORTAMIENTO ANTE PICOS DE CARGA                                     |
+---------------------------------------------------+-----------------------------------+
|  Métrica y Umbral:                                |  [VIDEO DEMO 4 / LIVE DEMO]       |
|  - CPU Target: 70% promedio por Pod               |  Duración: 25-30 segundos         |
|  - Réplicas: Min = 2 | Max = 6                    |                                   |
|                                                   |  Contenido del Video:             |
|  Script de Carga Sintética:                       |  1. Ejecución de test_hpa_scaling |
|  $ python3 scripts/test_hpa_scaling.py \          |     con 20 hilos concurrentes.    |
|      --concurrency 20 --duration 60               |  2. Panel de 'kubectl get hpa -w' |
|                                                   |     viendo CPU subir al 85% y     |
|  Comportamiento de Negocio:                       |     réplicas escalar: 2 -> 4 -> 6.|
|  - Absorción de picos transaccionales.            |  3. Enfriamiento automático tras  |
|  - Desescalado gradual tras 60s de estabilización |     cesar la carga.               |
+---------------------------------------------------+-----------------------------------+
```

---

## Slide 8 | Validación del Sistema de Alarmas y Resiliencia

```text
+---------------------------------------------------------------------------------------+
|  DISPARO CONTROLADO DE ALARMAS DE OBSERVABILIDAD                                      |
+---------------------------------------------------+-----------------------------------+
|  Reglas de Alerta Evaluadas:                      |  [VIDEO DEMO 5 / SCREENSHOT]      |
|  1. HighHttpErrorRate: Tasa de 5xx > 10% en 1 min.|  Duración: 20-25 segundos         |
|  2. HighHttpLatency: Latencia p95 > 1.0 segundo.  |                                   |
|                                                   |  Contenido del Video:             |
|  Ejecución del Script:                            |  1. Ejecución de:                 |
|  $ python3 scripts/test_alerts.py --type all      |     $ python3 scripts/test_alerts |
|                                                   |  2. Interfaz web de Prometheus:   |
|  Ciclo de Alerta Comprobado:                      |     Alerta pasando a 'Pending' y  |
|  - Inactive -> Pending (30s) -> Firing            |     luego a 'Firing'.             |
|  - Notificación y panel de advertencia en Grafana |  3. Dashboard de Grafana en rojo  |
|    en tiempo real.                                |     marcando la anomalía.         |
+---------------------------------------------------+-----------------------------------+
```

---

## Slide 9 | Gestión de Costos FinOps y Centralización de Logs

```text
+---------------------------------------------------------------------------------------+
|  AUDITORÍA FINOPS (KUBECOST) Y REGISTROS (ELK)                                        |
+---------------------------------------------------+-----------------------------------+
|  Kubecost: Visibilidad Financiera de Infra        |  Pila ELK: Inteligencia de Logs   |
|  - Costo mensual proyectado por Pod y PVC.        |  - Elasticsearch + Kibana         |
|  - Eficiencia de CPU/RAM asignada vs utilizada.   |  - Centralización de logs stdout. |
|  - Detección de sobredimensionamiento.            |  - Búsqueda del momento exacto    |
|                                                   |    del SIGTERM y códigos 503.     |
+---------------------------------------------------+-----------------------------------+
|  [ESPACIO PARA CAPTURA DE PANTALLA / VIDEO 6]                                         |
|  Dashboard de Kubecost mostrando coste de Namespace 'recreate-lab' y panel de Kibana. |
+---------------------------------------------------------------------------------------+
```

---

## Slide 10 | Conclusiones y Retorno de Inversión Técnico

```text
+---------------------------------------------------------------------------------------+
|  SÍNTESIS EJECUTIVA Y EVALUACIÓN DE IMPACTO                                           |
+---------------------------------------------------------------------------------------+
|  1. Cuándo usar Recreate con Confianza:                                               |
|     - Cuando la consistencia de datos supera el costo de unos segundos de corte.      |
|     - Arquitecturas con almacenamiento exclusivo RWO o cambios de esquema en BD.      |
|                                                                                       |
|  2. La Observabilidad como Factor Mitigador:                                          |
|     - El downtime deja de ser una "caja negra": se mide, se audita y se alerta.       |
|     - Las métricas RED y los logs en ELK permiten justificar el corte ante el cliente.|
|                                                                                       |
|  3. Eficiencia y Gobernanza:                                                          |
|     - HPA optimiza recursos y Kubecost asegura control estricto del presupuesto.      |
+---------------------------------------------------------------------------------------+
|  ¿Preguntas y Discusión Técnica?                                                      |
+---------------------------------------------------------------------------------------+
```

