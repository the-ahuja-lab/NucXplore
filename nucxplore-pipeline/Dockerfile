# syntax=docker/dockerfile:1.7

# === Build stage: builds nucxplore wheel from local checkout ===
FROM python:3.12-slim AS builder-source

ENV DEBIAN_FRONTEND=noninteractive
ENV RUSTUP_HOME=/opt/rust
ENV CARGO_HOME=/opt/rust

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --default-toolchain 1.88.0 --profile minimal --no-modify-path
ENV PATH="/opt/rust/bin:${PATH}"

WORKDIR /src
COPY nucxplore /src/nucxplore

RUN python -m pip install --upgrade pip && \
    python -m pip install "maturin>=1.5,<2.0"

RUN cd /src/nucxplore && maturin build --release --out /dist --interpreter python

# === Production image: installs nucxplore + runtime deps ===
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/usr/sbin/nologin" \
    --no-create-home \
    --uid "10001" \
    appuser

WORKDIR /work

COPY --from=builder-source /dist /tmp/dist
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir \
      /tmp/dist/nucxplore-*.whl \
      "numpy>=1.24,<1.27" \
      "pandas>=2.0,<2.3" \
      "joblib==1.5.2" \
      "threadpoolctl>=3.0,<4.0" \
      "xgboost==3.1.3" \
      "scikit-learn==1.8.0" \
      "scipy>=1.10,<1.15" \
      "pillow>=10.0,<11.0" \
      && rm -rf /tmp/dist

COPY nucxplore-pipeline/bin/cell_type_predict.py /usr/local/bin/cell_type_predict.py
RUN chmod +x /usr/local/bin/cell_type_predict.py

RUN mkdir -p /opt/nucxplore/models
COPY nucxplore-pipeline/models/xgboost_best_model.pkl /opt/nucxplore/models/xgboost_best_model.pkl
COPY nucxplore-pipeline/models/label_encoder.pkl /opt/nucxplore/models/label_encoder.pkl
COPY nucxplore-pipeline/models/model_manifest.json /opt/nucxplore/models/model_manifest.json

USER appuser
