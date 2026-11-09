# ==============================================================================
# Dockerfile: Frontend SPA React + Vite para Marea Dulce (NGINX Alpine)
# ==============================================================================

# Etapa 1: Compilación de la aplicación estática
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Etapa 2: Servidor Web NGINX ligero de alto rendimiento
FROM nginx:1.25-alpine

# Eliminar configuración por defecto de NGINX
RUN rm -rf /etc/nginx/conf.d/*

# Copiar configuración personalizada de proxy y SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar artefactos estáticos compilados desde la etapa anterior
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
