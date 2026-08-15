# NucXplore User Guide

Use this guide for package installation and common API calls. Detailed examples and troubleshooting live in [`../../wiki/Package-User-Guide.md`](../../wiki/Package-User-Guide.md).

## Install

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  "nucxplore[batch]==0.3.0"
```

NumPy is installed automatically. The `batch` extra installs Pillow and SciPy
for image/MAT file workflows. Python 3.10 or newer is required.

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
    feature_schema="legacy",  # legacy | dual | v2
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

Crops are masked raw-image patches written under `nuclei/`. Feature CSVs retain
the legacy `pre_norm_*` and `post_norm_*` columns for model compatibility. The
former are calculated from the raw tile and the latter from the mandatory
Vahadane-normalized tile, so paired values are generally different.

Use `feature_schema="dual"` to retain model-compatible columns and append all
corrected V2 features. Use `feature_schema="v2"` for the standalone 90-column
corrected schema. The current model cannot predict from V2-only CSVs. Definitions
and column accounting are in [Feature Schemas](feature-schemas.md).

The bundled model uses 126 legacy inputs, including 46 `post_norm_*` fields and
all seven corrected Hu moments. Do not alter feature names or substitute
unnormalized values before prediction.

## GPU Behavior

| Setting | Behavior |
|---|---|
| `use_gpu=False` | Force CPU execution. |
| `use_gpu=True` | Require compatible WGPU adapter. |
| `use_gpu=None` | Use package default. |

Run `nx.check_gpu()` to check adapter availability.

## Pipeline Users

For whole-slide crop/filtering, RGCI/HEIP segmentation, NucXplore extraction, and XGBoost prediction, use [`../../nucxplore-pipeline/`](../../nucxplore-pipeline/).
