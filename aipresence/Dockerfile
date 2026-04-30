# ---- Stage 1: Build frontend ----
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY client/package.json client/package-lock.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# ---- Stage 2: Build Python wheels (needed for armv7 which lacks pre-built wheels) ----
FROM python:3.13-slim AS python-deps
WORKDIR /wheels

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ gfortran libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# ---- Stage 3: Runtime ----
FROM python:3.13-slim
WORKDIR /app

# Install jq for parsing /data/options.json in run.sh, and libopenblas for numpy/sklearn runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends jq libopenblas0 \
    && rm -rf /var/lib/apt/lists/*

# Install pre-built wheels from stage 2 (no compiler needed)
COPY --from=python-deps /wheels /tmp/wheels
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels

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
