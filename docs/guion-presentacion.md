# Guion de Presentación Slide por Slide

---

## Ficha de Operación y Roles

- **Expositores:** Esteban Guarín Valencia y Juan José Arias Gallego.
- **Audiencia:** Líder Técnico / Jefe de Proyecto / Docente Evaluador.
- **Tono:** Profesional, técnico, seguro, directo y enfocado en resultados medibles.
- **Duración máxima sugerida:** 5 a 6 minutos.

---

## Slide 1 | Portada y Contexto Ejecutivo
- **Responsable:** Juan José Arias Gallego (0:00 - 0:30)
- **Qué mostrar en pantalla:** Slide 1 con los nombres formales y datos del clúster Minikube.
- **Qué hacer:** Saludar, presentar el título del proyecto y definir el alcance de la entrega.
- **Qué decir:**
  > "Buenos días. Hoy les presentamos los resultados de la implementación de la estrategia de despliegue Recreate y la arquitectura de observabilidad integral sobre Kubernetes. Nuestro objetivo fue llevar a la práctica un escenario real donde la consistencia de los datos exige un despliegue no concurrente, instrumentando toda la plataforma para que cada segundo de corte, cada recurso y cada peso consumido esté rigurosamente medido y controlado."

---

## Slide 2 | Justificación de Arquitectura: Estrategia Recreate
- **Responsable:** Juan José Arias Gallego (0:30 - 1:00)
- **Qué mostrar en pantalla:** Slide 2 con la comparativa RollingUpdate vs Recreate y el diagrama de flujo.
- **Qué hacer:** Enfatizar la justificación técnica de la decisión.
- **Qué decir:**
  > "Por defecto, Kubernetes aplica RollingUpdate para asegurar cero downtime. Sin embargo, en escenarios críticos donde existen migraciones destructivas de bases de datos o volúmenes persistentes en modo ReadWriteOnce, la coexistencia de dos versiones corrompe el sistema. Aplicar `strategy.type: Recreate` fue una decisión deliberada: preferimos un downtime controlado y planificado de pocos segundos a una inconsistencia de datos irrecuperable. Lo que nos diferencia es que no asumimos ese corte a ciegas; construimos la telemetría para medirlo y auditarlo con precisión."

---

## Slide 3 | Arquitectura Global de la Plataforma
- **Responsable:** Esteban Guarín Valencia (1:00 - 1:30)
- **Qué mostrar en pantalla:** Slide 3 con el mapa de componentes desacoplados.
- **Qué hacer:** Explicar cómo interactúan los bloques de red, carga de trabajo y observabilidad.
- **Qué decir:**
  > "A nivel de arquitectura, todo corre en un namespace aislado `recreate-lab`. La aplicación está blindada con una NetworkPolicy que solo permite tráfico HTTP desde el Ingress y recolección de métricas desde Prometheus. Además, desacoplamos el almacenamiento con un PVC persistente de 1 GiB montado en `/data`, y configuramos sondas de liveness y readiness para controlar con exactitud cuándo un contenedor está listo para recibir tráfico."

---

## Slide 4 | Régimen Nominal (Versión 1.0.0 Activa)
- **Responsable:** Esteban Guarín Valencia (1:30 - 2:00)
- **Qué mostrar en pantalla:** Slide 4 con el Video Demo 1 o demostración en vivo de la aplicación nominal.
- **Qué hacer:** Mostrar la aplicación web en azul (`v1.0.0`), el contador del PVC incrementando y Grafana marcando 0% de errores.
- **Qué decir:**
  > "Aquí vemos el régimen nominal. En pantalla observamos la interfaz azul de la versión 1.0.0 atendida por 2 réplicas. El contador persistido en disco `/data` está funcionando atómicamente. Al mismo tiempo, en Grafana monitoreamos la línea base RED: 10 peticiones por segundo, 100% de éxito con código 200 y latencia inferior a 15 milisegundos."

---

## Slide 5 | Demostración Central: Actualización Recreate y Medición de Downtime
- **Responsable:** Esteban Guarín y Juan José Arias (2:00 - 3:00)
- **Qué mostrar en pantalla:** Slide 5 con el Video Demo 2 (terminal con traffic generator y Lens/kubectl).
- **Qué hacer:**
  - Esteban narra la telemetría en la terminal de tráfico.
  - Juan José narra el ciclo de vida de los Pods en Kubernetes.
- **Qué decir (Juan José):**
  > "En este momento ejecutamos `kubectl apply -f k8s/deployment-v2.yaml`. Observen en la derecha cómo Kubernetes envía inmediatamente la señal SIGTERM a los Pods de la versión 1. Durante este instante no hay ningún pod listo para recibir tráfico."
- **Qué decir (Esteban):**
  > "Y en la izquierda, nuestro script `traffic_generator.py` captura el impacto en tiempo real: las conexiones devuelven HTTP 503 o caídas de socket. Inmediatamente después, los Pods de la versión 2 arrancan, superan la readinessProbe y el tráfico se restablece. El script calcula el downtime exacto: 6.45 segundos de indisponibilidad total."

---

## Slide 6 | Verificación Post-Corte: Versión 2.0 y Persistencia
- **Responsable:** Juan José Arias Gallego (3:00 - 3:30)
- **Qué mostrar en pantalla:** Slide 6 con el Video Demo 3 (navegador en verde y comprobación de archivo en disco).
- **Qué hacer:** Refrescar la página web y validar que el archivo en el PVC no perdió el historial.
- **Qué decir:**
  > "Comprobamos los resultados post-despliegue: la aplicación ahora responde en color verde identificando la versión 2.0.0. Y lo más importante: al consultar el contador persistente, confirmamos que mantuvo la cuenta acumulada de la versión 1. La estrategia Recreate cumplió su objetivo: reemplazo total sin corrupción de datos en el volumen."

---

## Slide 7 | Prueba de Carga y Autoescalado Horizontal (HPA)
- **Responsable:** Esteban Guarín Valencia (3:30 - 4:00)
- **Qué mostrar en pantalla:** Slide 7 con el Video Demo 4 (script de carga y `kubectl get hpa -w`).
- **Qué hacer:** Explicar cómo el sistema responde ante aumentos masivos de transacciones.
- **Qué decir:**
  > "Para evaluar la resiliencia ante fechas de alta demanda comercial, implementamos una regla de HPA con umbral del 70% de CPU. Con nuestro script `test_hpa_scaling.py` lanzamos 20 hilos concurrentes que simulan carga computacional. En el video se aprecia cómo el controlador detecta el aumento al 85% de CPU y escala automáticamente de 2 a 4 y luego a 6 réplicas para mitigar el cuello de botella, estabilizándose de nuevo al cesar la carga."

---

## Slide 8 | Validación del Sistema de Alarmas
- **Responsable:** Esteban Guarín Valencia (4:00 - 4:30)
- **Qué mostrar en pantalla:** Slide 8 con el Video Demo 5 (ejecución de `test_alerts.py` y dashboard de alertas).
- **Qué hacer:** Mostrar la transición de las alertas a estado `Firing`.
- **Qué decir:**
  > "La observabilidad debe ser proactiva. Diseñamos dos alarmas clave: tasa de errores 5xx superior al 10% y degradación de latencia por encima de 1 segundo. Con el script `test_alerts.py` forzamos ráfagas anómalas y verificamos en Prometheus cómo la alerta pasa de Inactive a Pending y a Firing, alertando visualmente en Grafana para que el equipo de soporte reaccione antes de que el cliente escale el reclamo."

---

## Slide 9 | Gestión de Costos FinOps y Centralización de Logs
- **Responsable:** Juan José Arias Gallego (4:30 - 5:00)
- **Qué mostrar en pantalla:** Slide 9 con capturas/videos de Kubecost y Kibana.
- **Qué hacer:** Conectar la técnica con el valor económico y la auditoría forense.
- **Qué decir:**
  > "Para cerrar el ciclo de gobernanza, desplegamos Kubecost y la pila ELK. Kubecost nos permite auditar en tiempo real el costo financiero de este despliegue, demostrando la eficiencia de CPU y memoria solicitada frente a la realmente consumida. Y en Kibana centralizamos los logs stdout de todos los Pods, permitiendo correlacionar el momento exacto del corte de Recreate con los registros de acceso."

---

## Slide 10 | Conclusiones y Ronda de Preguntas
- **Responsable:** Esteban Guarín y Juan José Arias (5:00 en adelante)
- **Qué mostrar en pantalla:** Slide 10 con los puntos de cierre ejecutivos.
- **Qué decir:**
  > "En conclusión, demostramos que la estrategia Recreate es perfectamente viable y segura cuando está respaldada por una observabilidad integral que mide el downtime, un autoescalado que absorbe demanda y una gestión estricta de costos y almacenamiento. Quedamos a su disposición para cualquier pregunta técnica."
