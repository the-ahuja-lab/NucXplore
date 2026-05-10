# NucXplore

NucXplore provides fast nucleus-level feature extraction for histopathology images and a Docker-backed Nextflow pipeline for whole-slide cell-type prediction.

## What To Use

| Need | Use |
|---|---|
| Extract nucleus features from image + MAT masks in Python | [`nucxplore/`](nucxplore/) package |
| Run WSI crop, segmentation, feature extraction, and prediction end to end | [`nucxplore-pipeline/`](nucxplore-pipeline/) workflow |
| Read detailed operational docs | [`wiki/Home.md`](wiki/Home.md) |

## Python Package

```bash
python -m pip install nucxplore
```

```python
import nucxplore as nx

features = nx.extract_features_from_files("tile.png", "tile.mat", use_gpu=False)
print(len(features))
```

The MAT file must contain a 2D instance map where `0` is background and positive integer values identify nuclei.

## Nextflow Pipeline

```bash
nextflow run <org>/<repo> -r <tag> -profile docker \
  --slide_root /data/slides \
  --outdir /data/results
```

From a local checkout:

```bash
nextflow run . -profile docker \
  --slide_root /data/slides \
  --outdir /data/results
```

The pipeline defaults to `ahujalab/nucxplore-crop-filter:latest`, `ahujalab/nucxplore-rgci-seg:latest`, and `ahujalab/nucxplore-cell-type-prediction:latest`.

## Outputs

| Pipeline path | Contents |
|---|---|
| `features/` | Per-image NucXplore feature CSVs |
| `predictions/` | Feature CSVs annotated with `Predicted_Label` and `Confidence_Score` |
| `nuclei/` | Optional masked nucleus crop PNGs |
| `logs/` | Stage logs and manifests |

## More Documentation

- Package quick guide: [`nucxplore/docs/user-guide.md`](nucxplore/docs/user-guide.md)
- Pipeline quick guide: [`nucxplore-pipeline/docs/user-guide.md`](nucxplore-pipeline/docs/user-guide.md)
- Detailed wiki pages: [`wiki/Home.md`](wiki/Home.md)
- Docker and reference validation: [`wiki/Docker-and-Validation.md`](wiki/Docker-and-Validation.md)

## Validation

```bash
cd nucxplore && cargo test --tests
cd ../nucxplore-pipeline && bash tests/run_stub_pipeline_checks.sh
```
