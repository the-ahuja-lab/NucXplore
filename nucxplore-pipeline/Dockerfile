# syntax=docker/dockerfile:1.7

# === Production mode: installs nucxplore from PyPI ===
FROM python:3.12-slim AS runtime-pypi

ARG NUCXPLORE_VERSION=0.2.0

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

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir \
      "nucxplore==${NUCXPLORE_VERSION}" \
      "numpy>=1.24,<1.27" \
      "pandas>=2.0,<2.3" \
      "joblib>=1.3,<1.5" \
      "threadpoolctl>=3.0,<4.0" \
      "xgboost>=2.0,<2.2" \
      "scikit-learn>=1.3,<1.6" \
      "scipy>=1.10,<1.15" \
      "pillow>=10.0,<11.0"

COPY nucxplore-pipeline/bin/cell_type_predict.py /usr/local/bin/cell_type_predict.py
RUN chmod +x /usr/local/bin/cell_type_predict.py

RUN mkdir -p /opt/nucxplore/models
COPY model_output_HPT_Final_Holy/model_output_HPT_Final_Holy/Final_XGB_Model_FullData.pkl /opt/nucxplore/models/Final_XGB_Model_FullData.pkl
COPY model_output_HPT_Final_Holy/model_output_HPT_Final_Holy/final_label_encoder.pkl /opt/nucxplore/models/final_label_encoder.pkl

USER appuser

# === Source mode: builds nucxplore from local checkout ===
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

FROM python:3.12-slim AS runtime-source

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
      "joblib>=1.3,<1.5" \
      "threadpoolctl>=3.0,<4.0" \
      "xgboost>=2.0,<2.2" \
      "scikit-learn>=1.3,<1.6" \
      "scipy>=1.10,<1.15" \
      "pillow>=10.0,<11.0" \
      && rm -rf /tmp/dist

COPY nucxplore-pipeline/bin/cell_type_predict.py /usr/local/bin/cell_type_predict.py
RUN chmod +x /usr/local/bin/cell_type_predict.py

RUN mkdir -p /opt/nucxplore/models
COPY model_output_HPT_Final_Holy/model_output_HPT_Final_Holy/Final_XGB_Model_FullData.pkl /opt/nucxplore/models/Final_XGB_Model_FullData.pkl
COPY model_output_HPT_Final_Holy/model_output_HPT_Final_Holy/final_label_encoder.pkl /opt/nucxplore/models/final_label_encoder.pkl

USER appuser
