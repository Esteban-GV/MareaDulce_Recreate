**Integrantes:**
Esteban Guarin Valencia
Juan Jose Arias Gallego

---
Estrategias de Despliegue con kubernetes

Exponer
- Aplicacion en vivo
- -5 minutos.
	
Chequear Terraform con Kubernetes
Instalar Lens

Metricas
- Recursos
- Estado
- Rendimiento
- Metricas de Negocio (Impacto a los usuarios).

Importancia de Metricas en Kubernetes
Las metricas deben cumplir con
- Especificas
- Accionables
- RElevantes
- Oportinas
- Medibles

Piramede de Monitoreo
- Recursos fidicos y virtuales
- Metricas de Kebernetes y sus componentes
- Metricas de los srevicios y aplicaciones que se ejecutan en el cluster

Dos modelos
- RED
- USE

Kubernetes recompilacion de metricas
- Daemon Sets
- Sidecards

- Prometheus
- Visualizacion: Grafana, Hibana, DataDog
- Alertas: 
- Pipelines de Datos de las metricas.
- Conocer el estado

Metricas
- Metricas de Infra. 
- Metricas de Cluster.
- Metricas de Pods.
- Metricas de Red.
- Metricas de Aplicación.

Cuales son las metricas de Infra?
Metricas de Red
Metricas de Cluster, cosas del ETCD, API Server Etc etc.

Capacidad total del cluster vs la usada.

Metricas
- Estado de un Pod. Running 
- Tasa de reinicio
- Tiempo de los Pods
- Pods no programados

Healchecks
- Verificar si la app está funcionando
- Verificar si la app está lista para recibir
- Tiempo de respuesta

Alertar
- No superar el 80%
- Latencia elevada de la API
- Etc


Ingress - Egress

Metricas para la HPA

Metricas para el Almacenamiento el PVC etc etc.

Con lo que vamos a levantar del despliegue cada uno tenemos que implementar un sistema de observabilidad. Poder visualizar como esos despliegues con las métricas como van operando.


Monitoreo Descentralizado y
Sencillito

Monitoreo Distribuido
Complejo

Si podemos montar un LK = Bonus

Metricas va primero.
Metricas - Logs - Traces

Crear modulo de Kubernetes, Service Mesh
Una cuenta verificada. Determinar si es B2B - B2C

Presentación de despliegue con observabilidad.
