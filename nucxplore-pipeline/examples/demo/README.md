# Demo pipeline

The demo launcher downloads checksum-pinned public example data and runs either
the complete NucXplore workflow or the final two stages from prepared
intermediates.

## Requirements

- Nextflow 25.04.7 or newer and Java 17+
- the `nucxplore-local` environment created from `../../environment.yml`
- Docker access
- `curl`, `sha256sum`, and `unzip`
- approximately 1 GB free for the intermediate demo
- several GB plus substantial CPU time for the full-slide demo

From the repository root, create the local environment once:

```bash
micromamba env create -f nucxplore-pipeline/environment.yml
```

## Full-slide example

This mode downloads `GTEX-1117F-0126.svs` and runs crop, segmentation, feature
extraction, and prediction. Segmentation uses CPU by default for portability.

```bash
bash nucxplore-pipeline/examples/demo/run_demo.sh full
```

Use an NVIDIA runtime configured for Docker and a segmentation image with a
CUDA-enabled PyTorch build to enable CUDA:

```bash
bash nucxplore-pipeline/examples/demo/run_demo.sh full --device cuda
```

Check `results/logs/segment.log` to confirm CUDA activation. The segmentation
CLI falls back to CPU with a warning when CUDA is unavailable inside the image.

The 328 MB slide can take a long time to segment on CPU. The demo publishes
the crop and segmentation intermediates so that every stage can be inspected.

## Intermediate example

This mode downloads `Sample_To_Test_Package.zip`, verifies and extracts its
eight matched PNG/MAT pairs, then runs feature extraction and prediction:

```bash
bash nucxplore-pipeline/examples/demo/run_demo.sh intermediate
```

The intermediate package contains tiles from `GTEX-1J8JJ-0626`; it is an
independent stage-resume example and is not derived from the full-demo SVS.

By default, data, Nextflow work files, and results are written beneath
`./nucxplore-demo/<mode>`. Choose another location or resume a stopped run with:

```bash
bash nucxplore-pipeline/examples/demo/run_demo.sh intermediate \
  --run-dir /data/nucxplore-demo/intermediate --resume
```

To avoid downloading files that already exist, put the exact release assets in
one directory and pass `--asset-dir /path/to/assets`. Checksums are always
verified before execution.

## Outputs

Results are written under the selected run directory:

| Path | Contents |
|---|---|
| `results/features/` | Per-tile nucleus feature CSVs and schema sidecars. |
| `results/predictions/` | Cell-type labels and confidence scores. |
| `results/logs/` | Stage manifests and execution logs. |
| `results/crops/` | Full-demo WSI crops. |
| `results/segmentation_mats/` | Full-demo instance maps. |

The source assets and their SHA-256 checksums are published in the
[`demo-data-v1` release](https://github.com/the-ahuja-lab/NucXplore/releases/tag/demo-data-v1).
