# NucXplore

`NucXplore` is a Rust + PyO3 Python package for high-throughput histopathology nucleus feature extraction.

The Nextflow workflow for crop/filtering, RGCI/HEIP segmentation, feature extraction, and cell-type prediction lives in the sibling `nucxplore-pipeline/` directory in this same repository. Runtime Docker images for pipeline execution are published on Docker Hub.

## Documentation

- User setup and usage: [`docs/user-guide.md`](docs/user-guide.md)
- Developer setup, validation, and release notes: [`docs/developer-guide.md`](docs/developer-guide.md)

## Install

```bash
python -m pip install nucxplore
```

Install the optional NumPy array API dependency only when calling the in-memory API:

```bash
python -m pip install "nucxplore[array]"
```

## Quick Start

```python
import nucxplore as nx

features = nx.extract_features_from_files(
    "/path/to/tile.png",
    "/path/to/tile.mat",
    mat_key=None,
    use_gpu=False,
)

print(len(features))
print(features[0].keys())
```

The `.mat` file must contain a 2D instance map where `0` is background and positive integer IDs identify nuclei.

## Main APIs

| API | Use case |
|---|---|
| `extract_features_from_files(...)` | Preferred dependency-light image + MAT file path. |
| `extract_features(...)` | In-memory NumPy image + mask extraction. |
| `save_cropped_nuclei_from_files(...)` | Save masked nucleus crops for one image/MAT pair. |
| `batch_extract_features(...)` | Batch feature extraction for paired image/MAT roots. |
| `batch_extract_and_crop(...)` | Batch extraction with crop export enabled by default. |
| `BatchExtractor(...)` | Reusable class API for batch workflows. |

GPU acceleration uses WGPU with CPU fallback support. NucXplore does not currently ship a separate CUDA-only wheel.
