# NucXplore Python Package

Rust + PyO3 package for high-throughput nucleus feature extraction from histopathology image tiles and MATLAB instance masks.

## Install

```bash
python -m pip install nucxplore
```

Install the optional NumPy extra for in-memory arrays:

```bash
python -m pip install "nucxplore[array]"
```

## Quick Start

```python
import nucxplore as nx

features = nx.extract_features_from_files(
    "tile.png",
    "tile.mat",
    mat_key=None,
    use_gpu=False,
)

print(len(features))
print(features[0]["nucleus_id"])
```

Input masks must be 2D instance maps: `0` for background and positive integer IDs for nuclei.

## Main APIs

| API | Use |
|---|---|
| `extract_features_from_files(...)` | Preferred file-based image + MAT extraction. |
| `extract_features(...)` | In-memory NumPy image + mask extraction. |
| `save_cropped_nuclei_from_files(...)` | Save masked crops for one image/MAT pair. |
| `batch_extract_features(...)` | Batch extraction for paired roots. |
| `batch_extract_and_crop(...)` | Batch extraction plus crop export. |
| `BatchExtractor(...)` | Reusable batch workflow class. |

## Documentation

- User guide: [`docs/user-guide.md`](docs/user-guide.md)
- Developer guide: [`docs/developer-guide.md`](docs/developer-guide.md)
- Detailed wiki: [`../wiki/Package-User-Guide.md`](../wiki/Package-User-Guide.md)

The full Nextflow workflow lives in [`../nucxplore-pipeline/`](../nucxplore-pipeline/).
