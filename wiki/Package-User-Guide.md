# Package User Guide

NucXplore is a Rust + PyO3 Python package for nucleus-level feature extraction from histopathology tiles and MATLAB instance masks.

## Install

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  "nucxplore[batch]==0.3.0"
```

Python 3.10+ and NumPy are required. The `batch` extra adds Pillow and SciPy for
image and MATLAB file workflows.

For local wheels:

```bash
python -m pip install /path/to/nucxplore-0.3.0-*.whl
```

## Input Contract

| Input | Requirement |
|---|---|
| Image file | RGB image tile readable by the Rust image loader. |
| MAT file | MATLAB v5 `.mat` file. |
| Instance map | 2D map with `0` as background and positive integer nucleus IDs. |
| `mat_key` | Optional; required when automatic MAT key detection is ambiguous. |
| Array image | NumPy `uint8` array shaped `(H, W, 3)`. |
| Array masks | NumPy instance map shaped `(H, W)` or sequence of boolean `(H, W)` masks. |

## File API

```python
import nucxplore as nx

features = nx.extract_features_from_files(
    "/data/images/tile.png",
    "/data/mats/tile.mat",
    mat_key=None,
    use_gpu=False,
)

print(len(features))
print(features[0]["nucleus_id"])
```

The file API loads image and MAT data in Rust and is the preferred dependency-light entrypoint.

## Array API

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

```python
features = nx.extract_features_from_files(
    "/data/images/tile.png",
    "/data/mats/tile.mat",
    save_crops=True,
    crop_output_dir="/data/results/nuclei",
    padding=10,
)
```

Output directories:

```text
/data/results/nuclei/nuclei/
```

Use `save_cropped_nuclei_from_files(...)` when only crop images and crop records are needed.

## Batch API

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

print(result.tasks_discovered)
print(result.completed_images)
print(result.failed_images)
print(result.total_nuclei)
```

Pairing rule: for each image at `<image_root>/<relpath>.<ext>`, the MAT file must exist at `<mat_root>/<relpath>.mat`.

## Batch CLI

```bash
python scripts/batch_extract_and_crop.py \
  --image-root /data/images \
  --mat-root /data/mats \
  --output-csv-root /data/results/features \
  --output-nuclei-root /data/results/nuclei \
  --workers 4 \
  --recursive \
  --no-use-gpu
```

Important options:

| Option | Default | Use |
|---|---|---|
| `--image-exts` | `.png,.jpg,.jpeg,.tif,.tiff,.bmp` | Image extensions to scan. |
| `--mat-key` | unset | MAT instance-map key. |
| `--inst-type-key` | `inst_type` | Optional nucleus type key. |
| `--metadata-csv` | unset | Append metadata columns to output rows. |
| `--metadata-id-source` | `first_dir` | Derive metadata key from image path. |
| `--save-crops` / `--no-save-crops` | enabled | Save crop PNGs. |

## Feature Groups

Each nucleus record includes identity, geometry, shape, spatial, texture, H&E color, HOG, and CCSM-derived features. The legacy `pre_norm_*` and `post_norm_*` columns are both retained because the prediction model expects all 129 feature columns. They are calculated from the raw and mandatory Vahadane-normalized tiles respectively and are generally different. Crop export writes one masked raw crop per nucleus.

`feature_schema` accepts `legacy` (130 API columns), `dual` (219), or `v2`
(90). V2 stores one corrected raw-patch measurement per patch feature and adds
seven diagnostic/boundary measurements. Use `dual` when both normalized legacy
model fields and corrected V2 analysis fields are required.
See [`nucxplore/docs/feature-schemas.md`](../nucxplore/docs/feature-schemas.md).

Stain normalization is mandatory. The bundled `WSI_Sample_Adnan` model uses 46
`post_norm_*` fields and every Hu moment, so historical unnormalized features
are not equivalent prediction inputs.

## GPU Behavior

| Setting | Behavior |
|---|---|
| `use_gpu=False` | Force CPU execution. |
| `use_gpu=True` | Require a compatible WGPU adapter. |
| `use_gpu=None` | Use package default behavior. |

`check_gpu()` returns adapter availability. `get_gpu_device_count()` returns `1` when an adapter is available and `0` otherwise. The package does not ship a CUDA-only wheel.

## Troubleshooting

| Symptom | Check |
|---|---|
| MAT variable cannot be detected | Pass `mat_key` explicitly. |
| Shape mismatch | Image height/width must match the instance map. |
| NumPy import errors | Reinstall `nucxplore`; NumPy is a required dependency. |
| GPU request fails | Use `use_gpu=False` or configure a WGPU-compatible adapter. |
| Stale local behavior after Rust edits | Rebuild and reinstall the wheel or refresh `python/nucxplore/_core.abi3.so`. |
