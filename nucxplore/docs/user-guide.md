# NucXplore User Guide

This guide is for users installing and running the NucXplore Python package. Contributor setup, tests, packaging, and release details are in [`developer-guide.md`](developer-guide.md).

## Repository Boundary

This repository contains both the `nucxplore` Python package and the `nucxplore-pipeline/` Nextflow workflow. The package provides feature extraction APIs and batch helpers. The pipeline handles WSI crop/filtering, RGCI/HEIP segmentation, extraction, and prediction using DockerHub runtime images. Users install the package from PyPI and run the pipeline via `nextflow run <org>/<repo>` — the two release processes are independent.

## Install

### Standard Runtime

```bash
python -m pip install nucxplore
```

This install is enough for the file API. Image and MATLAB loading happen in Rust, so the file API does not require Python `numpy`, `pillow`, or `scipy` at runtime.

### NumPy Array API

```bash
python -m pip install "nucxplore[array]"
```

Use this extra when calling `extract_features(image, masks, ...)` with in-memory NumPy arrays.

### Pre-release From TestPyPI

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  nucxplore
```

With the array extra:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  "nucxplore[array]"
```

### Local Wheel

```bash
python -m pip install /path/to/nucxplore-0.2.0-*.whl
```

## Input Contract

| Input | Requirement |
|---|---|
| Image | RGB image readable by NucXplore. |
| MAT mask | MATLAB v5 `.mat` file containing a 2D instance map. |
| Instance map values | `0` is background; positive integer values are nucleus IDs. |
| Array image | `uint8` NumPy array with shape `(H, W, 3)`. |
| Array masks | `uint32` instance map with shape `(H, W)` or sequence of boolean `(H, W)` masks. |

If `mat_key=None`, the file API auto-detects a suitable 2D instance map. Set `mat_key` when the MAT file contains multiple candidate arrays.

## Basic Usage

### File API

```python
import nucxplore as nx

features = nx.extract_features_from_files(
    "/data/images/tile.png",
    "/data/masks/tile.mat",
    mat_key=None,
    use_gpu=False,
)

print(len(features))
print(features[0]["nucleus_id"])
```

### Array API

```python
import numpy as np
import nucxplore as nx

image = np.zeros((64, 64, 3), dtype=np.uint8)
instance_map = np.zeros((64, 64), dtype=np.uint32)
instance_map[16:28, 20:32] = 1
instance_map[36:48, 34:46] = 2

features = nx.extract_features(image, instance_map, use_gpu=False)
```

## Crop Export

Save masked nucleus crops while extracting features:

```python
import nucxplore as nx

features = nx.extract_features_from_files(
    "/data/images/tile.png",
    "/data/masks/tile.mat",
    save_crops=True,
    crop_output_dir="/data/results/nuclei",
    padding=10,
)
```

Crop outputs are written under:

```text
/data/results/nuclei/pre_normalized_nuclei/
/data/results/nuclei/post_normalized_nuclei/
```

Use `save_cropped_nuclei_from_files(...)` when you only need crop images and per-nucleus crop records.

## Batch Usage

Use paired image and MAT roots when relative paths match:

```python
from nucxplore.batch import batch_extract_and_crop

result = batch_extract_and_crop(
    image_root="/data/images",
    mat_root="/data/mats",
    output_csv_root="/data/results/features",
    output_nuclei_root="/data/results/nuclei",
    workers=4,
    recursive=True,
    use_gpu=False,
)

print(result.processed)
print(result.failed)
```

The legacy script path is still available:

```bash
python scripts/batch_extract_and_crop.py --help
```

## Feature Output

Each nucleus record includes:

| Feature group | Examples |
|---|---|
| Identity and geometry | `nucleus_id`, centroid, bounding box, area, perimeter. |
| Shape | Hu moments, advanced shape features, NEIS features. |
| Spatial | nearest-neighbor distance. |
| Pre-normalized image features | intensity, GLCM, LBP, H&E color, HOG, CCSM. |
| Post-normalized image features | `post_norm_` intensity, GLCM, LBP, H&E color, HOG, CCSM. |

By default, the normalized image is the input image. Set `NUQR_ENABLE_STAIN_NORMALIZATION=1` only for runs that intentionally require Vahadane post-normalization.

## GPU Behavior

| Setting | Behavior |
|---|---|
| `use_gpu=False` | Force CPU execution. |
| `use_gpu=True` | Require a compatible WGPU adapter; fail if unavailable. |
| `use_gpu=None` | Use package default behavior. |

`check_gpu()` reports whether a compatible adapter is available. `get_gpu_device_count()` returns `1` when an adapter is available and `0` otherwise. NucXplore does not currently provide a separate CUDA wheel.

## Troubleshooting

| Symptom | Check |
|---|---|
| MAT variable cannot be detected | Pass `mat_key=<name>` explicitly. |
| Image/MAT shape mismatch | Confirm the instance map has the same height and width as the image. |
| NumPy import or typing errors | Install `python -m pip install "nucxplore[array]"`. |
| GPU request fails | Run with `use_gpu=False` or install/configure a WGPU-compatible adapter stack. |
| Stale local behavior after Rust changes | Rebuild and reinstall the wheel; source-tree imports can load an old `_core.abi3.so`. |

## Pipeline Users

For whole-slide crop/filtering, RGCI/HEIP segmentation, NucXplore extraction, and XGBoost prediction, see the `nucxplore-pipeline/` directory in this repository. Run the hosted pipeline via `nextflow run <org>/<repo> -r <tag> -profile docker` or `nextflow run ./nucxplore-pipeline` from a local checkout. Runtime Docker images are published on Docker Hub separately from the PyPI package.
