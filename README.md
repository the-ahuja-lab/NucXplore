# NucXplore

High-performance histopathology nucleus feature extraction library and Nextflow cell-type prediction pipeline.

## Source Layout

| Path | Purpose |
|---|---|
| `nucxplore/` | Rust + PyO3 Python package — feature extraction library. Install from PyPI. |
| `nucxplore-pipeline/` | Nextflow workflow — crop, segment, extract features, predict cell types. |
| `plans/` | Development planning notes and migration guides. |

## Library (pip install)

```bash
python -m pip install nucxplore
```

```python
import nucxplore as nx
features = nx.extract_features_from_files("tile.png", "tile.mat")
```

See `nucxplore/docs/user-guide.md` for full API docs.

## Pipeline (Nextflow)

Run directly from the hosted GitHub repository:

```bash
nextflow run <org>/<repo> -r <tag> -profile docker \
  --slide_root /data/slides \
  --outdir /data/results \
  --crop_filter_container ... \
  --seg_container ... \
  --container ...
```

Run from a local checkout:

```bash
nextflow run .
```

Development: `nextflow run ./nucxplore-pipeline` or `cd nucxplore-pipeline && nextflow run .`

See `nucxplore-pipeline/docs/user-guide.md` for parameters and troubleshooting.

## Release Boundary

- **PyPI wheels** are built from `nucxplore/` and published on package-specific tags (`nucxplore-v*`). Pipeline code is never included in the wheel.
- **Docker images** for pipeline execution are maintained separately and published manually to Docker Hub.
- **GitHub Actions** validate and publish the package only; pipeline validation runs locally.

## Validation

| Component | Environment | Command (from component dir) |
|---|---|---|
| Package (Rust) | `rustenv` | `cargo test --tests` |
| Package (Python) | `rustenv` | `python -m py_compile python/nucxplore/batch.py scripts/batch_extract_and_crop.py` |
| Pipeline (stub) | `nextflow` | `bash tests/run_stub_pipeline_checks.sh` |
| Pipeline (Python) | `nextflow` | `python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py` |
