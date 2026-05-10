# NucXplore User Guide

Use this guide for package installation and common API calls. Detailed examples and troubleshooting live in [`../../wiki/Package-User-Guide.md`](../../wiki/Package-User-Guide.md).

## Install

```bash
python -m pip install nucxplore
```

Use `python -m pip install "nucxplore[array]"` for the in-memory NumPy API.

## Input Contract

| Input | Requirement |
|---|---|
| Image file | RGB tile readable by NucXplore. |
| MAT file | MATLAB v5 file containing a 2D instance map. |
| Instance map | `0` is background; positive integers are nucleus IDs. |
| Array image | `uint8` NumPy array shaped `(H, W, 3)`. |
| Array masks | `(H, W)` instance map or sequence of boolean `(H, W)` masks. |

Set `mat_key` when a MAT file contains multiple candidate arrays.

## File API

```python
import nucxplore as nx

features = nx.extract_features_from_files(
    "/data/images/tile.png",
    "/data/masks/tile.mat",
    mat_key=None,
    use_gpu=False,
)
```

## Array API

```python
import numpy as np
import nucxplore as nx

image = np.zeros((64, 64, 3), dtype=np.uint8)
instance_map = np.zeros((64, 64), dtype=np.uint32)
instance_map[16:28, 20:32] = 1

features = nx.extract_features(image, instance_map, use_gpu=False)
```

## Batch Extraction

```python
from nucxplore.batch import batch_extract_and_crop

result = batch_extract_and_crop(
    image_root="/data/images",
    mat_root="/data/mats",
    output_csv_root="/data/results/features",
    output_nuclei_root="/data/results/nuclei",
    workers=4,
)

print(result.completed_images)
print(result.failed_images)
print(result.total_nuclei)
```

## Crop Export

```python
features = nx.extract_features_from_files(
    "/data/images/tile.png",
    "/data/masks/tile.mat",
    save_crops=True,
    crop_output_dir="/data/results/nuclei",
)
```

Crops are written under `pre_normalized_nuclei/` and `post_normalized_nuclei/`.

## GPU Behavior

| Setting | Behavior |
|---|---|
| `use_gpu=False` | Force CPU execution. |
| `use_gpu=True` | Require compatible WGPU adapter. |
| `use_gpu=None` | Use package default. |

Run `nx.check_gpu()` to check adapter availability.

## Pipeline Users

For whole-slide crop/filtering, RGCI/HEIP segmentation, NucXplore extraction, and XGBoost prediction, use [`../../nucxplore-pipeline/`](../../nucxplore-pipeline/).
