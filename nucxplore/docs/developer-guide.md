# NucXplore Developer Guide

This guide is for contributors working on the Rust/PyO3 package library. User installation and API examples are in [`user-guide.md`](user-guide.md).

## Repository Boundary

This repository builds and ships the `nucxplore` Python package from the `nucxplore/` directory. The Nextflow workflow lives in the sibling `nucxplore-pipeline/` directory within the same repository. Pipeline runtime images should depend on released package wheels from PyPI, not on an unpublished source-tree checkout.

## Source Layout

| Path | Purpose |
|---|---|
| `src/lib.rs` | PyO3 module entrypoint and Python API wiring. |
| `src/features/` | CPU feature implementations and extraction pipeline. |
| `src/gpu/` | WGPU backends and WGSL shader pipelines. |
| `src/io/` | Rust image and MATLAB v5 readers for the dependency-light file API. |
| `src/stain_norm/` | Vahadane stain normalization implementation. |
| `python/nucxplore/` | Python package wrapper, type stubs, and `py.typed`. |
| `scripts/` | Developer and compatibility CLIs. |
| `tests/` | Rust integration tests and Python API tests. |
| `benches/` | Criterion benchmark suite. |
| `examples/` | User-facing examples and notebooks. |

## Dependency Model

| Context | Dependencies |
|---|---|
| File API runtime | No required Python dependencies. |
| Array API runtime | `numpy`, installed by `pip install "nucxplore[array]"`. |
| Development | `requirements.txt` or `pip install -e .[dev]` equivalent when supported by the workflow. |
| Packaging | Rust toolchain plus `maturin`. |

## Local Setup

Activate the `rustenv` micromamba environment, then build and install:

```bash
micromamba activate rustenv
python -m pip install -r requirements.txt
maturin build --release --out dist --interpreter python
python -m pip install --force-reinstall --no-deps dist/nucxplore-*.whl
```

When importing with `PYTHONPATH=python`, rebuild after Rust changes so `python/nucxplore/_core.abi3.so` is current. A stale extension can cause parity regressions unrelated to source code.

## Core Validation

Run commands from `nucxplore/`:

```bash
cargo fmt --all
cargo test --tests
python -m py_compile python/nucxplore/batch.py scripts/batch_extract_and_crop.py
```

Run documentation-sensitive Rust checks when public Rust docs change:

```bash
cargo rustdoc --lib -- -W missing-docs -D rustdoc::invalid_html_tags
```

## API Contracts To Preserve

| API | Contract |
|---|---|
| `extract_features` | Accepts `(H, W, 3)` `uint8` image and either `(H, W)` `uint32` instance map or sequence of `(H, W)` boolean masks. |
| `extract_features_from_files` | Loads image and MAT in Rust, expands `~/`, validates shape compatibility, and auto-detects MAT key when omitted. |
| `save_cropped_nuclei_from_files` | Writes `pre_normalized_nuclei/` and/or `post_normalized_nuclei/` and returns per-nucleus crop records. |
| `batch_extract_and_crop` | Writes per-image CSVs and nucleus crop PNGs for paired image/MAT roots. |
| `BatchExtractor` | Reusable class API for batch extraction and crop export. |

`inst_type` loading is best effort through SciPy when available. Missing or unavailable `inst_type` should remain non-fatal and default `nucleus_type` to `Unknown`.

## Batch And Script Notes

Keep reusable orchestration in `python/nucxplore/batch.py`. `scripts/batch_extract_and_crop.py` should stay a thin wrapper around `nucxplore.batch.main()`.

Useful checks:

```bash
cargo test crop_export -- --nocapture
cargo test test_full_pipeline_end_to_end_cpu
PYTHONPATH=python python scripts/batch_extract_and_crop.py --help
```

Comparison modes:

```bash
python scripts/compare_with_python_features.py --extractor-api direct
python scripts/compare_with_python_features.py --extractor-api files
```

## Profiling And Benchmarks

| Tool | Command |
|---|---|
| Numerical validation | `cargo run --release --bin numerical_validation` |
| CPU profiling | `cargo run --release --bin cpu_profile` |
| Memory profiling | `cargo run --release --bin memory_profile` |
| Criterion benchmarks | `cargo bench --bench benchmark_suite` |

Capture baseline numbers before performance edits and preserve CPU fallback behavior.

## Packaging And Publishing

Packaging is configured in `pyproject.toml` using maturin. The package name is `nucxplore`, and the compiled extension is `nucxplore._core`.

### GitHub Actions Workflows

| File | Purpose |
|---|---|
| `.github/workflows/package-ci.yml` | PR/push validation for `nucxplore/` changes. Runs `cargo fmt`, `cargo test`, and Python syntax checks. |
| `.github/workflows/publish-pypi.yml` | Release build and PyPI publish triggered by `nucxplore-v*` tags or manual `workflow_dispatch`. Builds one ABI3 wheel per OS (covers Python 3.8+) and an sdist. |

### Release Steps

1. Push a tag matching `nucxplore-v*` (e.g., `nucxplore-v0.2.0`), or trigger the workflow manually via the Actions tab.
2. The publish workflow builds one ABI3 wheel per OS (Linux, macOS, Windows). A single ABI3 wheel covers all supported Python versions (3.8–3.12). An sdist is also built.
3. PyPI publication uses trusted publishing (`id-token: write`).

### Trusted Publishing Setup

Before the first PyPI release:

1. Go to https://pypi.org/manage/projects/nucxplore/settings/.
2. Add a new trusted publisher:
   - GitHub repository: `<org>/<repo>`
   - Workflow name: `publish-pypi.yml`
   - Environment name: `pypi`
   - (Optional) Restrict to tags matching `nucxplore-v*`.

### TestPyPI

Manual `workflow_dispatch` on the publish workflow. Before running, configure a second trusted publisher or use a `TEST_PYPI_API_TOKEN` secret.

The Rust dependency graph for release wheels should stay free of `native-tls` and `openssl-sys` unless there is a deliberate release decision.

## GPU Policy

NucXplore uses WGPU for optional cross-platform acceleration. Standard wheels are GPU-capable on supported systems. Do not add CUDA-only runtime assumptions to the package API unless a future release explicitly introduces a separate CUDA distribution.

## Documentation And Typing

| File | Maintainer responsibility |
|---|---|
| `README.md` | Keep as concise repository entrypoint. |
| `docs/user-guide.md` | Keep user setup and usage current. |
| `docs/developer-guide.md` | Keep contributor workflow current. |
| `python/nucxplore/__init__.pyi` | Update when Python API signatures change. |
| `python/nucxplore/_core.pyi` | Update when compiled API signatures change. |
| `python/nucxplore/py.typed` | Preserve in packaged wheels. |

Add `CHANGELOG.md` entries for user-visible behavior changes, public API changes, and durable documentation changes.
