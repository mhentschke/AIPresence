# ---- Stage 1: Build frontend ----
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY client/package.json client/package-lock.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# ---- Stage 2: Python runtime ----
FROM python:3.13-slim
WORKDIR /app

# Install jq for parsing /data/options.json in run.sh
RUN apt-get update \
    && apt-get install -y --no-install-recommends jq \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from stage 1
COPY --from=frontend-build /build/dist ./frontend/

# Copy entrypoint script
COPY run.sh ./
RUN chmod +x run.sh

ENV STATIC_DIR=/app/frontend
ENV DATA_PATH=/data

ENTRYPOINT ["/app/run.sh"]
