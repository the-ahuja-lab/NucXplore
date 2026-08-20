# NucXplore Python Package

NucXplore is a Rust/PyO3 package for deterministic nucleus-level feature
extraction from histopathology image tiles and MATLAB instance masks.

## Requirements and installation

- Python 3.10+
- NumPy 1.24+
- Pillow and SciPy for file and batch workflows

Install version 0.3.0 from the project release channel:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  "nucxplore[batch]==0.3.0"
```

For local development, build and install a wheel instead:

```bash
maturin build --release --out dist --interpreter python
python -m pip install --force-reinstall "dist/nucxplore-0.3.0-"*.whl
```

## Input contract

| Input | Contract |
|---|---|
| RGB image | `uint8`, shape `(height, width, 3)`. |
| Instance map | Same height/width; `0` is background and positive integers are nucleus IDs. |
| MAT input | MATLAB v5 file containing one suitable 2D instance map, or an explicit `mat_key`. |

## Quick start

```python
import nucxplore as nx

features = nx.extract_features_from_files(
    "tile.png",
    "tile.mat",
    mat_key="inst_map",
    use_gpu=False,
    feature_schema="legacy",
)

print(nx.__version__)
print(len(features), features[0]["nucleus_id"])
```

Stain normalization is always applied once to the complete tile. In `legacy`
and `dual`, raw-patch values use the `pre_norm_*` prefix and normalized-patch
values use `post_norm_*`. Normalization failures are reported; raw values are
never silently substituted.

## Feature schemas

| Schema | API columns | Notes |
|---|---:|---|
| `legacy` | 130 | Default and required by the bundled 129-feature classifier. |

## Public APIs

| API | Purpose |
|---|---|
| `extract_features(...)` | Extract from in-memory NumPy arrays. |
| `extract_features_from_files(...)` | Load one image/MAT pair and extract features. |
| `save_cropped_nuclei_from_files(...)` | Export masked raw-image nucleus crops. |
| `batch_extract_features(...)` | Extract paired directory trees. |
| `batch_extract_and_crop(...)` | Extract features and optionally export crops. |
| `BatchExtractor(...)` | Configure and reuse a batch workflow. |
| `check_gpu()` | Report whether a WGPU adapter is available. |

## Batch example

```python
from nucxplore.batch import batch_extract_and_crop

result = batch_extract_and_crop(
    image_root="/data/images",
    mat_root="/data/mats",
    output_csv_root="/data/results/features",
    output_nuclei_root="/data/results/nuclei",
    workers=8,
    mat_key="inst_map",
    feature_schema="legacy",
    save_crops=False,
)

assert result.failed_images == 0
print(result.completed_images, result.total_nuclei)
```

Images and MAT files are paired by relative path and filename stem. Each CSV
has a `.csv.schema.json` sidecar recording schema, feature count, algorithm
revision, padding, and mandatory normalization.

## Validation

```bash
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets --all-features
python -m pytest -q tests
```

## Documentation

- [User guide](docs/user-guide.md)
- [Feature definitions and evidence](docs/feature-schemas.md)
- [Developer guide](docs/developer-guide.md)
- [Repository pipeline](../nucxplore-pipeline/README.md)

## License

[MIT](LICENSE)
