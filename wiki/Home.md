# NucXplore Wiki

This directory contains GitHub-wiki-ready pages for detailed NucXplore documentation. The repository READMEs and `docs/` guides stay concise; long-form operational content lives here.

## Pages

| Page | Contents |
|---|---|
| [Package User Guide](Package-User-Guide.md) | Install, inputs, APIs, crops, batch extraction, GPU behavior. |
| [Pipeline User Guide](Pipeline-User-Guide.md) | Full and partial Nextflow runs, input modes, outputs, troubleshooting. |
| [Pipeline Parameters](Pipeline-Parameters.md) | Current `nextflow.config` parameter reference. |
| [Docker and Validation](Docker-and-Validation.md) | Docker image contracts, local image build/run helpers, reference CSV validation. |
| [Developer Guide](Developer-Guide.md) | Contributor workflows for package and pipeline maintenance. |

## Repository Components

| Component | Path | Release boundary |
|---|---|---|
| Python package | `nucxplore/` | PyPI package built with maturin from tags such as `nucxplore-v*`. |
| Nextflow pipeline | `nucxplore-pipeline/` | Docker-backed workflow released independently from package wheels. |
| Docker reference CSVs | `Docker_References/` when present in the workspace | Validation data generated from a verified Docker run. |

## Quick Links

- Public package README: `nucxplore/README.md`
- Public pipeline README: `nucxplore-pipeline/README.md`
- Pipeline params file example: `nucxplore-pipeline/params.example.yaml`
- Stub validation: `cd nucxplore-pipeline && bash tests/run_stub_pipeline_checks.sh`
