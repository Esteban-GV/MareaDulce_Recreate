# ==============================================================================
# Dockerfile: Microservicio Python para Demostración de Recreate y Observabilidad
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Prevenir escritura de archivos .pyc y forzar salida stdout sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Instalar dependencias de producción
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ /app/src/

# Crear punto de montaje para el volumen persistente (PVC)
RUN mkdir -p /data && chmod 777 /data

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
