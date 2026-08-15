# NucXplore Developer Guide

Contributor guide for the Rust/PyO3 package. Detailed maintenance notes live in [`../../wiki/Developer-Guide.md`](../../wiki/Developer-Guide.md).

## Layout

| Path | Purpose |
|---|---|
| `src/lib.rs` | PyO3 module entrypoint. |
| `src/features/` | CPU feature extraction. |
| `src/gpu/` | WGPU acceleration. |
| `src/io/` | Rust image and MATLAB readers. |
| `python/nucxplore/` | Python wrappers, stubs, and `py.typed`. |
| `tests/` | Rust and Python integration checks. |

## Local Build

```bash
python -m pip install -r requirements.txt
maturin build --release --out dist --interpreter python
python -m pip install --force-reinstall --no-deps dist/nucxplore-*.whl
```

If using `PYTHONPATH=python`, rebuild after Rust changes so `python/nucxplore/_core.abi3.so` is current.

## Validate

```bash
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets --all-features
python -m pytest -q tests
python -m py_compile python/nucxplore/batch.py scripts/batch_extract_and_crop.py
```

## Public API Files

Update these together when signatures change:

| File | Purpose |
|---|---|
| `python/nucxplore/__init__.py` | Public Python package exports and wrappers. |
| `python/nucxplore/_core.pyi` | Compiled extension type stubs. |
| `python/nucxplore/batch.pyi` | Batch API type stubs. |
| `docs/user-guide.md` | Public user examples. |

Add changelog entries for user-visible behavior, API, and durable documentation changes.

Generated `target/`, `dist/`, compiled extension, cache, and coverage outputs
must remain untracked. Model artifacts belong to the pipeline component, not
the Python wheel.
