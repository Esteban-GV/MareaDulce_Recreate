# Persistencia de Datos y Autoescalado Horizontal

---

## 1. Persistencia de Datos con PersistentVolumeClaim (PVC)

La estrategia Recreate es comúnmente obligatoria en escenarios con almacenamiento exclusivo. El proyecto implementa un volumen desacoplado para asegurar la durabilidad de los datos entre ciclos de vida de réplicas:

- **Manifiesto:** [`k8s/pvc.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/pvc.yaml)
- **Modo de Acceso:** `ReadWriteOnce` (RWO), garantizando que solo un Pod a la vez monte el volumen en modo lectura y escritura.
- **Capacidad Solicitada:** 1 GiB gestionado por el StorageClass predeterminado de Minikube.
- **Punto de Montaje:** Montado en `/data` dentro del contenedor del microservicio.
- **Validación Práctica:** El microservicio almacena y lee un contador acumulativo en `/data/counter.txt`. Cuando la versión 1.0 es destruida y nace la versión 2.0, el contador retoma el valor previo sin pérdida de información, evidenciando la persistencia.

---

## 2. Autoescalado Horizontal de Pods (HPA)

El recurso [`k8s/hpa.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/hpa.yaml) asegura la adaptabilidad de la infraestructura ante variaciones de demanda:

- **Métrica Objetivo:** 70% de utilización promedio de CPU.
- **Rango de Réplicas:** Mínimo 2 réplicas y máximo 6 réplicas.
- **Justificación de Negocio:**
  - Garantiza dimensionamiento adecuado en horarios de baja demanda (ahorro de costos auditado por Kubecost).
  - Escala reactivamente ante picos transaccionales o fechas críticas de negocio (campañas comerciales o cierres contables).
- **Políticas de Comportamiento:**
  - *Scale Up:* Inmediato (estabilización en 0s, duplicación de réplicas en 15s).
  - *Scale Down:* Controlado (ventana de estabilización de 60s para evitar fluctuaciones rápidas o *flapping*).

