# Feature Schemas

NucXplore exposes three explicit feature schemas through `feature_schema`.
Vahadane stain normalization is always enabled. Legacy and dual schemas
calculate `pre_norm_*` from the raw patch and `post_norm_*` from the normalized
patch. There is no unnormalized extraction mode.

Algorithm revision `v3.0` also calculates all Hu columns with the valid
raw-moment → central-moment → normalized-central-moment → Hu sequence. Earlier
reference CSVs mostly contained zero Hu values and duplicated post-normalization
values; they remain useful as historical comparison data, not as the v3.0
scientific contract.

| Schema | API columns per nucleus | Purpose |
|---|---:|---|
| `legacy` | 130 | Current 129-feature XGBoost model plus `nucleus_id`. |
| `dual` | 219 | All 130 legacy columns plus all 89 corrected V2 features. |
| `v2` | 90 | `nucleus_id` plus 89 unique corrected features. |

These are core API counts. Pipeline CSVs also include `nucleus_type` and batch
CSV files may include requested metadata columns; those are annotations, not
model features.

`legacy` remains the default. The model requires its 129 named legacy features;
therefore prediction accepts `legacy` and `dual`, while a V2-only CSV fails with
a missing-model-features error.

## Why V2 Has 90 Columns

The legacy schema contains 47 patch measurements under both `pre_norm_*` and
`post_norm_*`. V2 intentionally stores one corrected raw-patch measurement per
feature rather than carrying both normalization namespaces:

```text
35 non-patch features + 47 patch features + 7 V2 diagnostics = 89 features
89 features + nucleus_id = 90 columns
```

Use `dual` when corrected V2 measurements and the current model-compatible
pre/post columns are both required.

### Original Sample_For_Adnan evidence

The prefixes were originally intended to represent different measurements:

- `pre_norm_*`: features calculated before stain normalization.
- `post_norm_*`: features calculated after stain normalization.

That distinction did not occur in the original generated data. We audited all
CSV files under `Sample_For_Adnan/GTEX-1F75B-0126_Features` by pairing every
`pre_norm_X` column with `post_norm_X` and comparing aligned nucleus rows.

| Statistic | Verified result |
|---|---:|
| Original CSV files | 248 |
| Nuclei | 79,321 |
| Pre/post feature pairs | 47 |
| Total paired values | 3,728,087 |
| Exactly identical feature pairs | 47/47 |
| Feature pairs with any difference | 0/47 |
| Different paired values | 0 |
| Percentage identical | 100.0% |
| Mean absolute difference | 0 |
| Maximum absolute difference | 0 |
| Pairs equal within `rtol=1e-12, atol=1e-12` | 47/47 |
| Paired NaN values | 168 |
| NaN mismatches | 0 |

Paired NaNs were treated as equal. Across all finite observations, each
relationship is therefore exactly:

```text
pre_norm_X == post_norm_X
```

The audit demonstrates that the 47 post-normalization columns contain no
additional measurements in the original reference dataset. This is consistent
with the effective feature-generation path: Python attempted SNMF stain
normalization but could silently fall back to the raw image, while Rust did not
enable normalization by default. The restored implementation defaults to
normalization, uses deterministic initialization, and propagates failures
instead of silently substituting the raw patch.

The schema policy follows from those results:

- `legacy` preserves both names because the deployed XGBoost model was trained
  against the complete 129-name legacy input contract.
- `dual` preserves that contract and appends the corrected V2 measurements, so
  prediction and corrected scientific analysis can run from one output.
- `v2` stores each unique patch measurement once. Reintroducing the 47 aliases
  merely to raise the count above 120 would duplicate data, create perfect
  collinearity, increase storage and compute costs downstream, and provide no
  new biological information.

### V3.0 real-tile validation

The release wheel was run twice on the real 1,250×1,250 tile
`GTEX-1F75B-0126_tile_11250_5000` with its real MATLAB instance map.

| Statistic | Result |
|---|---:|
| Nuclei | 366 |
| Numeric model features | 129 |
| Finite numeric outputs | 100% |
| Pre/post pairs with any changed value | 46/47 |
| Exact paired-value rate | 7.2143% |
| Median pre/post Pearson correlation | 0.756279 |
| Minimum pre/post Pearson correlation | -0.928896 |
| Hu 1/2 nonzero nuclei | 366/366 |
| Repeated CSV files byte-identical | yes |
| Runtime | 8.4 seconds |
| Peak resident memory | approximately 182 MB |

Using the classifier bundled before 2026-08-14 on both inputs, v3.0 Rust
features versus the original Python feature values produced 99.7268% label
agreement (365/366) and 0.999916 confidence correlation. This is retained as a
historical extractor-parity result, not a benchmark for the current model.

The classifier installed from `WSI_Sample_Adnan` on 2026-08-14 uses 126 of the
129 inputs, including 46 `post_norm_*` features and all seven Hu moments. It
therefore requires the mandatory v3.0 normalization and corrected-Hu semantics;
predictions from the previous classifier are not expected to match it.

An earlier exploratory comparison appeared to show tiny differences in three
CCSM pairs. That result came from comparing a separate older generated-output
directory, not the original `Sample_For_Adnan` reference CSVs. The direct audit
of the original files above supersedes that interpretation: all 47 original
pre/post pairs are exactly identical.

### Reproduction

The validation should align rows by tile and `nucleus_id`, coerce paired columns
to numeric values, compare finite values exactly, and separately count paired
NaNs and NaN mismatches. The repository validation utility also checks the
fresh legacy output against the reference dataset:

```bash
python nucxplore-pipeline/scripts/validate_sample_correlation.py \
  --generated-features /path/to/generated/features \
  --reference Sample_For_Adnan/GTEX-1F75B-0126_Features \
  --min-correlation 0.9979587292
```

A fresh V2.1 legacy regeneration completed 249 paired extraction tasks with no
failures and produced 79,321 nuclei across the 248 non-empty reference CSVs.
All 47 generated pre/post pairs were exactly equal; all 129 common reference
features met the threshold, with minimum Pearson correlation
`0.9979587292356816`.

## V2 Feature Dictionary

Every feature below has a `v2_` prefix in CSV/API output.

| Group | Count | Fields |
|---|---:|---|
| Morphology | 22 | `area`, `perimeter`, `equivalent_diameter`, `major_axis_length`, `minor_axis_length`, `eccentricity`, `solidity`, `extent`, `convex_area`, `euler_number`, `orientation`, `centroid_row`, `centroid_col`, `circularity`, `aspect_ratio`, `hu_moment_1` … `hu_moment_7` |
| Advanced shape | 9 | `convexity`, `fractal_dimension`, `roughness`, `bending_energy`, `fourier_descriptor_1` … `fourier_descriptor_5` |
| NEIS | 3 | `neis_irregularity_score`, `neis_spectral_energy`, `neis_spectral_peak_mode` |
| Intensity | 10 | `mean_intensity`, `median_intensity`, `std_intensity`, `min_intensity`, `max_intensity`, `range_intensity`, `iqr_intensity`, `skewness_intensity`, `kurtosis_intensity`, `entropy_intensity` |
| GLCM | 6 | `glcm_contrast`, `glcm_dissimilarity`, `glcm_homogeneity`, `glcm_energy`, `glcm_correlation`, `glcm_ASM` |
| LBP | 3 | `lbp_mean`, `lbp_std`, `lbp_entropy` |
| H&E | 13 | six hematoxylin statistics, six eosin statistics, `he_ratio_H_to_E` |
| HOG | 4 | `hog_mean`, `hog_std`, `hog_max`, `hog_min` |
| CCSM | 11 | condensed-area ratio, clump count/area/eccentricity/solidity, boundary distance, nearest-neighbor distance, and four condensed-texture properties |
| Spatial | 1 | `distance_to_nearest_neighbor` |
| V2 diagnostics | 7 | `fractal_dimension_r2`, `fractal_dimension_scales`, `he_deconvolution_valid`, `boundary_gradient_mean`, `boundary_gradient_std`, `boundary_gradient_max`, `boundary_orientation_entropy` |

## Corrected Definitions

- Hu moments use raw moments → central moments → normalized central moments → Hu invariants.
- Fractal dimension is the least-squares slope of boundary box counts over
  power-of-two scales. Fewer than three valid scales yields zero; R² and scale
  count are reported.
- Fourier descriptors use 128 arc-length contour samples, centroid and RMS
  normalization, and paired positive/negative harmonics for start-point,
  traversal, translation, scale, rotation, and reflection invariance.
- H&E deconvolution normalizes the study H/E vectors, completes the 3×3 basis
  with their cross product, inverts the basis, and clips negative concentrations.
- GLCM pairs are counted only when both endpoints are inside the nucleus;
  genuine zero-intensity pixels remain valid.
- HOG uses 8 unsigned bins in 8×8 cells over the tight nucleus box. A gradient
  enters HOG only when its full axial stencil is inside the nucleus. Partial
  edge cells are retained and 1×1 blocks use L2-Hys normalization. Boundary
  gradients use mask-valid one-sided differences and are reported separately.
- CCSM uses masked CLAHE: exterior pixels contribute to neither intensity ranges
  nor contextual histograms. Empty tile maps are excluded and interpolation
  weights are renormalized. The deterministic two-component GMM and condensed
  GLCM also operate only on valid masked pixels/pairs.

Corrected V2 HOG and masked CLAHE/CCSM always use the deterministic CPU
implementation, even when `use_gpu=True`. Legacy GPU behavior is unchanged.

Degenerate or empty measurements return finite zeros unless the field is an
explicit validity/count diagnostic. Per-tile `.csv.schema.json` sidecars record
the selected schema, feature count, `algorithm_revision: "v3.0"`, padding, and
always-enabled stain normalization.
