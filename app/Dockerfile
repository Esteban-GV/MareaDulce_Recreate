# ==============================================================================
# Dockerfile: Marea Dulce — Plataforma Cloud-Native (Recreate Deployment)
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Instalar dependencias de producción
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente y estáticos del Frontend SPA
COPY src/ /app/src/
COPY static/ /app/static/

# Crear punto de montaje para el volumen persistente (PVC SQLite)
RUN mkdir -p /data && chmod 777 /data

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
