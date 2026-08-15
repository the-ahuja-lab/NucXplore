# Package and Module Version Inventory

This inventory records the package versions used by the NucXplore workflow. It
was verified from the source imports, Cargo lockfile, Nextflow configuration,
local Micromamba environments, and the two published Docker images.

## Pipeline orchestration

| Package or tool | Version | Purpose |
|---|---:|---|
| Nextflow | 26.04.0 | Pipeline orchestration |
| OpenJDK | 22.0.1 | Nextflow runtime |
| Segmentation image | `ahujalab/nucxplore-seg:latest` | HEIP nuclear segmentation |
| Prediction image | `ahujalab/nucxplore-cell-type-prediction:latest` | Feature extraction and XGBoost prediction |
| Micromamba base image | 1.5.10 | Segmentation environment construction |

The pipeline configuration is defined in `nucxplore-pipeline/nextflow.config`.

## Crop and feature-extraction environment

The crop, sample preparation, pair-discovery, and per-tile feature-extraction
stages use the local `nucxplore-local` Micromamba environment.

| Package | Installed version | Purpose |
|---|---:|---|
| Python | 3.10.20 | Runtime |
| NucXplore | **0.2.0** | Feature extraction |
| NumPy | 2.2.6 | Image arrays |
| Pillow | 12.0.0 | Image reading and writing |
| TIFFSlide | 2.5.1 | Whole-slide image access |
| SciPy | 1.15.2 | MAT-file loading |
| tifffile | 2025.5.10 | TIFF support |
| imagecodecs | 2025.3.30 | TIFF compression codecs |

### Important local-version mismatch

`nucxplore-pipeline/environment.yml` specifies `nucxplore==0.3.0`, but the
currently installed `nucxplore-local` environment contains NucXplore 0.2.0.
Consequently, a local feature-extraction run may not use the latest Hu-moment,
Vahadane normalization, and feature-schema implementation. Update or recreate
this environment before using it for production results.

NumPy, Pillow, and TIFFSlide are not version-pinned in `environment.yml`, so a
new environment solve may install versions different from those listed above.

## Rust NucXplore feature module

The NucXplore package version is 0.3.0. These are the exact direct dependency
versions resolved in `nucxplore/Cargo.lock`.

| Rust crate | Resolved version | Function |
|---|---:|---|
| `pyo3` | 0.22.6 | Python bindings |
| `numpy` | 0.22.1 | NumPy/Rust interoperability |
| `ndarray` | 0.16.1 | Multidimensional arrays |
| `rayon` | 1.11.0 | Parallel feature generation |
| `rustfft` | 6.4.1 | Fourier descriptors |
| `num-complex` | 0.4.6 | Complex FFT values |
| `statrs` | 0.17.1 | Statistical calculations |
| `image` | 0.25.10 | Image structures and operations |
| `imageproc` | 0.25.0 | Morphology and contours |
| `wgpu` | 0.19.4 | GPU acceleration |
| `bytemuck` | 1.25.0 | GPU buffer conversion |
| `pollster` | 0.3.0 | WGPU asynchronous execution |
| `futures-intrusive` | 0.5.0 | GPU buffer synchronization |
| `tracing` | 0.1.44 | Logging |
| `tracing-subscriber` | 0.3.23 | Log configuration |
| `serde` | 1.0.228 | Serialization |
| `thiserror` | 1.0.69 | Structured errors |
| `anyhow` | 1.0.102 | General error propagation |

Development and build dependencies:

| Package or tool | Version |
|---|---:|
| `criterion` | 0.5.1 |
| `approx` | 0.5.1 |
| Rust toolchain used by Docker | 1.88.0 |
| Maturin | `>=1.5,<2.0` |

The Python package metadata additionally declares:

| Dependency group | Requirement |
|---|---|
| Core | `numpy>=1.24,<3` |
| Batch extra | `pillow>=10,<12`, `scipy>=1.10,<2` |
| Development | `numpy>=1.24,<3`, `pytest>=7.0`, `pytest-benchmark>=4.0`, `pillow>=10.0`, `scikit-image>=0.19`, `scipy>=1.7` |

## Segmentation module

The following versions are installed in the published
`ahujalab/nucxplore-seg:latest` image.

| Package | Installed version |
|---|---:|
| Python | 3.9.25 |
| PyTorch | 1.13.1 |
| TorchVision | 0.14.1 |
| TorchAudio | 0.13.1 |
| PyTorch CUDA | 11.7 |
| cellseg-models-pytorch | 0.1.16 |
| PyTorch Lightning | 1.9.5 |
| OmegaConf | 2.3.0 |
| timm | 0.6.13 |
| NumPy | 1.23.5 |
| SciPy | 1.13.1 |
| scikit-image | 0.19.3 |
| scikit-learn | 1.6.1 |
| Pillow | 9.5.0 |
| OpenCV Python | 4.11.0.86 |
| ImageIO | 2.37.2 |
| PyWavelets | 1.6.0 |
| tifffile | 2024.8.30 |
| numba | 0.57.1 |
| llvmlite | 0.40.1 |
| tqdm | 4.67.3 |
| torchmetrics | 1.5.2 |
| lightning-utilities | 0.15.2 |
| huggingface-hub | 1.8.0 |
| networkx | 3.2.1 |
| joblib | 1.5.3 |
| threadpoolctl | 3.6.0 |
| PyYAML | 6.0.3 |

The authoritative environment definition is
`nucxplore-pipeline/envs/nucxplore-seg.yml`. The root-level
`NewHEIP_05052026.yml` is a larger captured development environment and is not
the environment used to build the production segmentation image.

## Cell-type prediction image

The following versions are installed in the published
`ahujalab/nucxplore-cell-type-prediction:latest` image.

| Package | Installed version |
|---|---:|
| Python | 3.12 |
| NucXplore | 0.3.0 |
| XGBoost | 3.1.3 |
| scikit-learn | 1.8.0 |
| NumPy | 1.26.4 |
| pandas | 2.2.3 |
| SciPy | 1.14.1 |
| Pillow | 10.4.0 |
| joblib | 1.5.2 |
| threadpoolctl | 3.6.0 |
| NVIDIA NCCL | 2.31.2 |
| python-dateutil | 2.9.0.post0 |
| pytz | 2026.3.post1 |
| tzdata | 2026.3 |
| six | 1.17.0 |

The prediction container bundles:

- `xgboost_best_model.pkl`
- `label_encoder.pkl`
- `model_manifest.json`

Its build definition is `nucxplore-pipeline/Dockerfile`.

## Reproducibility notes

- The Rust dependency graph is reproducible through `Cargo.lock`.
- The prediction image directly constrains its primary Python dependencies and
  records the versions resolved during the published build.
- The segmentation environment pins its principal application packages but not
  every transitive dependency. Rebuilding it later can therefore change some
  indirect package versions.
- The local environment leaves NumPy, Pillow, and TIFFSlide unpinned.
- The local NucXplore installation must be upgraded from 0.2.0 to 0.3.0 to
  match the repository and prediction image.

## Source files

- `nucxplore/Cargo.toml`
- `nucxplore/Cargo.lock`
- `nucxplore/pyproject.toml`
- `nucxplore/requirements.txt`
- `nucxplore-pipeline/environment.yml`
- `nucxplore-pipeline/envs/nucxplore-seg.yml`
- `nucxplore-pipeline/Dockerfile`
- `nucxplore-pipeline/Dockerfile.nucxplore-seg`
- `nucxplore-pipeline/nextflow.config`
- `nucxplore-pipeline/conf/containers.config`
