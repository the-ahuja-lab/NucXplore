# Demo

NucXplore provides a local launcher and a hosted Google Colab notebook. Choose
the hosted notebook when you want to try the demo without installing the
package, Nextflow, Java, Conda, or Docker on your computer.

## Run in Google Colab

Open the [NucXplore Colab notebook](https://colab.research.google.com/drive/1OrYK8HZeysp_6L0-d-HAzV_kf2ZhAks1?usp=sharing)
and follow its cells from top to bottom. Colab supplies the temporary runtime;
download any results you want to keep before ending the session.

## Run locally

The local launcher downloads checksum-verified assets from the
[`demo-data-v1` release](https://github.com/the-ahuja-lab/NucXplore/releases/tag/demo-data-v1).

Run the complete workflow on `GTEX-1117F-0126.svs`:

```bash
bash nucxplore-pipeline/examples/demo/run_demo.sh full
```

Run feature extraction and prediction from eight prepared PNG/MAT pairs:

```bash
bash nucxplore-pipeline/examples/demo/run_demo.sh intermediate
```

The full-slide example uses CPU segmentation by default and can take several
hours. Add `--device cuda` when Docker and the segmentation image expose a
working CUDA-enabled PyTorch runtime. See the repository
[demo guide](https://github.com/the-ahuja-lab/NucXplore/blob/main/nucxplore-pipeline/examples/demo/README.md)
for requirements, resume options, storage estimates, checksums, and outputs.
