//! Corrected, versioned feature implementations.
//!
//! These routines intentionally do not alter the historical feature contract.
//! All outputs are namespaced by the caller as `v2_*`.

use std::collections::HashMap;

use ndarray::{ArrayView2, ArrayView3};
use num_complex::Complex;
use rustfft::FftPlanner;

use crate::core::{FeaturizerError, Result};

fn finite(value: f64) -> f64 {
    if value.is_finite() {
        value
    } else {
        0.0
    }
}

/// Correct Hu pipeline: raw -> central -> normalized central -> Hu.
/// O(P) time and O(1) moment storage. f64 is retained throughout because
/// third-order moments are cancellation-sensitive.
pub fn hu(mask: &ArrayView2<bool>) -> HashMap<String, f64> {
    let raw = super::moments::moments_raw(mask, 3);
    let central = super::moments::moments_central(&raw.view(), mask);
    let normalized = super::moments::moments_normalized(&central.view());
    super::moments::moments_hu(&normalized.view())
        .iter()
        .enumerate()
        .map(|(i, &v)| (format!("hu_moment_{}", i + 1), finite(v)))
        .collect()
}

fn boundary(mask: &ArrayView2<bool>) -> Vec<(usize, usize)> {
    let (h, w) = mask.dim();
    let mut out = Vec::new();
    for r in 0..h {
        for c in 0..w {
            if !mask[[r, c]] {
                continue;
            }
            if r == 0
                || c == 0
                || r + 1 == h
                || c + 1 == w
                || !mask[[r - 1, c]]
                || !mask[[r + 1, c]]
                || !mask[[r, c - 1]]
                || !mask[[r, c + 1]]
            {
                out.push((r, c));
            }
        }
    }
    out
}

/// Boundary box-counting dimension. Power-of-two scales avoid arbitrary bin
/// widths; at least three non-degenerate scales are required for a fit.
/// O(B log L) time, where B is boundary length and L the maximum crop extent.
pub fn box_counting(mask: &ArrayView2<bool>) -> (f64, f64, f64) {
    let points = boundary(mask);
    let (h, w) = mask.dim();
    let mut sizes = Vec::new();
    let mut size = 1usize;
    while size <= h.max(w) / 2 {
        let mut boxes = std::collections::HashSet::new();
        for &(r, c) in &points {
            boxes.insert((r / size, c / size));
        }
        if boxes.len() > 1 {
            sizes.push(((1.0 / size as f64).ln(), (boxes.len() as f64).ln()));
        }
        size *= 2;
    }
    if sizes.len() < 3 {
        return (0.0, 0.0, sizes.len() as f64);
    }
    let n = sizes.len() as f64;
    let mx = sizes.iter().map(|p| p.0).sum::<f64>() / n;
    let my = sizes.iter().map(|p| p.1).sum::<f64>() / n;
    let sxx = sizes.iter().map(|p| (p.0 - mx).powi(2)).sum::<f64>();
    if sxx <= 1e-15 {
        return (0.0, 0.0, n);
    }
    let slope = sizes.iter().map(|p| (p.0 - mx) * (p.1 - my)).sum::<f64>() / sxx;
    let sst = sizes.iter().map(|p| (p.1 - my).powi(2)).sum::<f64>();
    let sse = sizes
        .iter()
        .map(|p| (p.1 - (my + slope * (p.0 - mx))).powi(2))
        .sum::<f64>();
    let r2 = if sst > 1e-15 { 1.0 - sse / sst } else { 1.0 };
    (finite(slope), finite(r2), n)
}

/// Arc-length resampling plus centering/RMS normalization removes translation
/// and scale. Pairing +/- FFT harmonics makes the magnitudes invariant to
/// contour start, traversal direction, rotation, and reflection.
pub fn fourier(mask: &ArrayView2<bool>) -> [f64; 5] {
    let Some(points) = super::shape::largest_external_contour(mask) else {
        return [0.0; 5];
    };
    if points.len() < 3 {
        return [0.0; 5];
    }
    let mut src: Vec<Complex<f64>> = points
        .iter()
        .map(|p| Complex::new(p.x as f64, p.y as f64))
        .collect();
    src.push(src[0]);
    let mut cumulative = vec![0.0; src.len()];
    for i in 1..src.len() {
        cumulative[i] = cumulative[i - 1] + (src[i] - src[i - 1]).norm();
    }
    let total = *cumulative.last().unwrap_or(&0.0);
    if total <= 1e-12 {
        return [0.0; 5];
    }
    let mut samples = Vec::with_capacity(128);
    let mut segment = 1usize;
    for i in 0..128 {
        let target = total * i as f64 / 128.0;
        while segment + 1 < cumulative.len() && cumulative[segment] < target {
            segment += 1;
        }
        let lo = cumulative[segment - 1];
        let span = cumulative[segment] - lo;
        let t = if span > 0.0 {
            (target - lo) / span
        } else {
            0.0
        };
        samples.push(src[segment - 1] * (1.0 - t) + src[segment] * t);
    }
    let center = samples.iter().copied().sum::<Complex<f64>>() / 128.0;
    for z in &mut samples {
        *z -= center;
    }
    let rms = (samples.iter().map(|z| z.norm_sqr()).sum::<f64>() / 128.0).sqrt();
    if rms <= 1e-12 {
        return [0.0; 5];
    }
    for z in &mut samples {
        *z /= rms;
    }
    let mut planner = FftPlanner::<f64>::new();
    planner.plan_fft_forward(128).process(&mut samples);
    let mut out = [0.0; 5];
    for k in 1..=5 {
        out[k - 1] = finite((samples[k].norm_sqr() + samples[128 - k].norm_sqr()).sqrt() / 128.0);
    }
    out
}

/// Mask-valid GLCM: a pair contributes only when both endpoints are nuclear.
/// True zero-valued nuclear pixels remain valid observations.
pub fn glcm(gray: &ArrayView2<f32>, mask: &ArrayView2<bool>) -> Result<HashMap<String, f64>> {
    if gray.dim() != mask.dim() {
        return Err(FeaturizerError::InvalidDimensions {
            expected: format!("{:?}", mask.dim()),
            got: format!("{:?}", gray.dim()),
        });
    }
    let offsets = [(0isize, 1isize), (-1, 1), (-1, 0), (-1, -1)];
    let mut sums = [0.0; 6];
    let mut valid_angles = 0.0;
    let (h, w) = gray.dim();
    for (dr, dc) in offsets {
        let mut matrix = vec![0u64; 256 * 256];
        let mut count = 0u64;
        for r in 0..h {
            for c in 0..w {
                let rr = r as isize + dr;
                let cc = c as isize + dc;
                if rr < 0
                    || cc < 0
                    || rr >= h as isize
                    || cc >= w as isize
                    || !mask[[r, c]]
                    || !mask[[rr as usize, cc as usize]]
                {
                    continue;
                }
                let a = gray[[r, c]].clamp(0.0, 255.0) as usize;
                let b = gray[[rr as usize, cc as usize]].clamp(0.0, 255.0) as usize;
                matrix[a * 256 + b] += 1;
                matrix[b * 256 + a] += 1;
                count += 2;
            }
        }
        if count == 0 {
            continue;
        }
        let denom = count as f64;
        let mut mi = 0.0;
        let mut mj = 0.0;
        for i in 0..256 {
            for j in 0..256 {
                let p = matrix[i * 256 + j] as f64 / denom;
                mi += i as f64 * p;
                mj += j as f64 * p;
            }
        }
        let mut vi = 0.0;
        let mut vj = 0.0;
        for i in 0..256 {
            for j in 0..256 {
                let p = matrix[i * 256 + j] as f64 / denom;
                vi += (i as f64 - mi).powi(2) * p;
                vj += (j as f64 - mj).powi(2) * p;
            }
        }
        let mut angle_asm = 0.0;
        for i in 0..256 {
            for j in 0..256 {
                let p = matrix[i * 256 + j] as f64 / denom;
                if p == 0.0 {
                    continue;
                }
                let d = (i as f64 - j as f64).abs();
                sums[0] += d * d * p;
                sums[1] += d * p;
                sums[2] += p / (1.0 + d * d);
                angle_asm += p * p;
                sums[5] += (i as f64 - mi) * (j as f64 - mj) * p / (vi * vj).sqrt().max(1e-15);
            }
        }
        sums[3] += angle_asm;
        sums[4] += angle_asm.sqrt();
        valid_angles += 1.0;
    }
    if valid_angles == 0.0 {
        valid_angles = 1.0;
    }
    let names = [
        "glcm_contrast",
        "glcm_dissimilarity",
        "glcm_homogeneity",
        "glcm_ASM",
        "glcm_energy",
        "glcm_correlation",
    ];
    Ok(names
        .iter()
        .enumerate()
        .map(|(i, n)| ((*n).to_string(), finite(sums[i] / valid_angles)))
        .collect())
}

/// Correct stain separation matrix. Study H/E vectors are normalized and a
/// cross-product residual completes the basis; inversion converts OD to stain
/// concentrations. The determinant check prevents unstable deconvolution.
pub fn he(rgb: &ArrayView3<u8>, mask: &ArrayView2<bool>) -> Result<HashMap<String, f64>> {
    let (h, w, c) = rgb.dim();
    if c != 3 || mask.dim() != (h, w) {
        return Err(FeaturizerError::InvalidDimensions {
            expected: format!("({h}, {w}, 3) and ({h}, {w})"),
            got: format!("{:?}, {:?}", rgb.dim(), mask.dim()),
        });
    }
    let norm = |v: [f64; 3]| {
        let n = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt();
        [v[0] / n, v[1] / n, v[2] / n]
    };
    let hv = norm([0.65, 0.70, 0.29]);
    let ev = norm([0.07, 0.99, 0.11]);
    let rv = norm([
        hv[1] * ev[2] - hv[2] * ev[1],
        hv[2] * ev[0] - hv[0] * ev[2],
        hv[0] * ev[1] - hv[1] * ev[0],
    ]);
    let m = [
        [hv[0], ev[0], rv[0]],
        [hv[1], ev[1], rv[1]],
        [hv[2], ev[2], rv[2]],
    ];
    let det = m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
    let mut out = HashMap::new();
    out.insert(
        "he_deconvolution_valid".into(),
        if det.abs() > 1e-10 { 1.0 } else { 0.0 },
    );
    if det.abs() <= 1e-10 {
        return Ok(out);
    }
    let inv = [
        [
            (m[1][1] * m[2][2] - m[1][2] * m[2][1]) / det,
            (m[0][2] * m[2][1] - m[0][1] * m[2][2]) / det,
            (m[0][1] * m[1][2] - m[0][2] * m[1][1]) / det,
        ],
        [
            (m[1][2] * m[2][0] - m[1][0] * m[2][2]) / det,
            (m[0][0] * m[2][2] - m[0][2] * m[2][0]) / det,
            (m[0][2] * m[1][0] - m[0][0] * m[1][2]) / det,
        ],
        [
            (m[1][0] * m[2][1] - m[1][1] * m[2][0]) / det,
            (m[0][1] * m[2][0] - m[0][0] * m[2][1]) / det,
            (m[0][0] * m[1][1] - m[0][1] * m[1][0]) / det,
        ],
    ];
    let mut hs = Vec::new();
    let mut es = Vec::new();
    for r in 0..h {
        for col in 0..w {
            if mask[[r, col]] {
                let od = [
                    -((rgb[[r, col, 0]] as f64 + 1.0) / 256.0).ln(),
                    -((rgb[[r, col, 1]] as f64 + 1.0) / 256.0).ln(),
                    -((rgb[[r, col, 2]] as f64 + 1.0) / 256.0).ln(),
                ];
                hs.push((inv[0][0] * od[0] + inv[0][1] * od[1] + inv[0][2] * od[2]).max(0.0));
                es.push((inv[1][0] * od[0] + inv[1][1] * od[1] + inv[1][2] * od[2]).max(0.0));
            }
        }
    }
    let stats = |v: &[f64]| {
        if v.is_empty() {
            return [0.0; 6];
        }
        let n = v.len() as f64;
        let mean = v.iter().sum::<f64>() / n;
        let var = v.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / n;
        let sd = var.sqrt();
        let skew = if sd > 1e-12 {
            v.iter().map(|x| ((x - mean) / sd).powi(3)).sum::<f64>() / n
        } else {
            0.0
        };
        let kurt = if sd > 1e-12 {
            v.iter().map(|x| ((x - mean) / sd).powi(4)).sum::<f64>() / n - 3.0
        } else {
            0.0
        };
        [
            mean,
            sd,
            skew,
            kurt,
            v.iter().copied().fold(f64::INFINITY, f64::min),
            v.iter().copied().fold(f64::NEG_INFINITY, f64::max),
        ]
    };
    let a = stats(&hs);
    let b = stats(&es);
    let labels = ["mean", "std", "skew", "kurt", "min", "max"];
    for i in 0..6 {
        out.insert(format!("{}_hematoxylin", labels[i]), finite(a[i]));
        out.insert(format!("{}_eosin", labels[i]), finite(b[i]));
    }
    out.insert(
        "he_ratio_H_to_E".into(),
        if b[0] > 1e-12 { a[0] / b[0] } else { 0.0 },
    );
    Ok(out)
}

/// Algorithm: mask-aware HOG with separate boundary-gradient summaries.
///
/// Time complexity: O(P + C), for P crop pixels and C 8x8 cells. Space is
/// O(P + 8C). Central differences are admitted only when the complete axial
/// stencil belongs to the nucleus, preventing the artificial zero background
/// from creating gradients. Per-cell L2-Hys uses f64 and an epsilon-protected
/// norm, so constant cells remain finite. Partial edge cells are retained,
/// which avoids systematically discarding small nuclei.
pub fn gradients(gray: &ArrayView2<f32>, mask: &ArrayView2<bool>) -> HashMap<String, f64> {
    const BINS: usize = 8;
    const CELL: usize = 8;
    const EPS: f64 = 1e-5;

    let (h, w) = gray.dim();
    let mut descriptor = Vec::new();
    let mut boundary_magnitudes = Vec::new();
    let mut boundary_bins = [0.0; BINS];

    let bounds = mask.indexed_iter().filter(|(_, &inside)| inside).fold(
        None,
        |acc: Option<(usize, usize, usize, usize)>, ((r, c), _)| {
            Some(match acc {
                None => (r, r, c, c),
                Some((r0, r1, c0, c1)) => (r0.min(r), r1.max(r), c0.min(c), c1.max(c)),
            })
        },
    );

    if let Some((r0, r1, c0, c1)) = bounds {
        let cell_rows = (r1 - r0 + 1).div_ceil(CELL);
        let cell_cols = (c1 - c0 + 1).div_ceil(CELL);
        let mut histograms = vec![[0.0_f64; BINS]; cell_rows * cell_cols];
        let mut valid_counts = vec![0usize; cell_rows * cell_cols];

        for r in r0..=r1 {
            for c in c0..=c1 {
                if !mask[[r, c]] {
                    continue;
                }
                let left = c > 0 && mask[[r, c - 1]];
                let right = c + 1 < w && mask[[r, c + 1]];
                let up = r > 0 && mask[[r - 1, c]];
                let down = r + 1 < h && mask[[r + 1, c]];
                let center = gray[[r, c]] as f64;
                let gx = match (left, right) {
                    (true, true) => (gray[[r, c + 1]] - gray[[r, c - 1]]) as f64,
                    (false, true) => gray[[r, c + 1]] as f64 - center,
                    (true, false) => center - gray[[r, c - 1]] as f64,
                    (false, false) => 0.0,
                };
                let gy = match (up, down) {
                    (true, true) => (gray[[r + 1, c]] - gray[[r - 1, c]]) as f64,
                    (false, true) => gray[[r + 1, c]] as f64 - center,
                    (true, false) => center - gray[[r - 1, c]] as f64,
                    (false, false) => 0.0,
                };
                let magnitude = gx.hypot(gy);
                let angle = gy.atan2(gx).rem_euclid(std::f64::consts::PI);
                let bin = ((angle / std::f64::consts::PI * BINS as f64) as usize).min(BINS - 1);
                let interior = left && right && up && down;
                if interior {
                    let cell_index = ((r - r0) / CELL) * cell_cols + (c - c0) / CELL;
                    histograms[cell_index][bin] += magnitude;
                    valid_counts[cell_index] += 1;
                } else {
                    boundary_magnitudes.push(magnitude);
                    boundary_bins[bin] += magnitude;
                }
            }
        }

        for (histogram, &count) in histograms.iter().zip(&valid_counts) {
            if count == 0 {
                continue;
            }
            let mut block = *histogram;
            let norm = (block.iter().map(|v| v * v).sum::<f64>() + EPS * EPS).sqrt();
            for value in &mut block {
                *value = (*value / norm).min(0.2);
            }
            let renorm = (block.iter().map(|v| v * v).sum::<f64>() + EPS * EPS).sqrt();
            descriptor.extend(block.iter().map(|value| value / renorm));
        }
    }

    let summary = |values: &[f64]| {
        if values.is_empty() {
            [0.0; 4]
        } else {
            let mean = values.iter().sum::<f64>() / values.len() as f64;
            let std = (values.iter().map(|v| (v - mean).powi(2)).sum::<f64>()
                / values.len() as f64)
                .sqrt();
            [
                mean,
                std,
                values.iter().copied().fold(0.0, f64::max),
                values.iter().copied().fold(f64::INFINITY, f64::min),
            ]
        }
    };
    let hog = summary(&descriptor);
    let edge = summary(&boundary_magnitudes);
    let total = boundary_bins.iter().sum::<f64>();
    let entropy = if total > 0.0 {
        -boundary_bins
            .iter()
            .filter(|&&v| v > 0.0)
            .map(|v| {
                let p = v / total;
                p * p.ln()
            })
            .sum::<f64>()
    } else {
        0.0
    };

    [
        ("hog_mean", hog[0]),
        ("hog_std", hog[1]),
        ("hog_max", hog[2]),
        ("hog_min", hog[3]),
        ("boundary_gradient_mean", edge[0]),
        ("boundary_gradient_std", edge[1]),
        ("boundary_gradient_max", edge[2]),
        ("boundary_orientation_entropy", entropy),
    ]
    .iter()
    .map(|(key, value)| ((*key).to_string(), finite(*value)))
    .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::Array2;

    fn ellipse(h: usize, w: usize, cy: f64, cx: f64, ry: f64, rx: f64) -> Array2<bool> {
        Array2::from_shape_fn((h, w), |(r, c)| {
            ((r as f64 - cy) / ry).powi(2) + ((c as f64 - cx) / rx).powi(2) <= 1.0
        })
    }

    #[test]
    fn corrected_hu_is_nonzero_and_translation_invariant() {
        let a = ellipse(100, 100, 45.0, 40.0, 15.0, 24.0);
        let b = ellipse(100, 100, 55.0, 58.0, 15.0, 24.0);
        let ha = hu(&a.view());
        let hb = hu(&b.view());
        assert!(ha["hu_moment_1"] > 0.0);
        for i in 1..=7 {
            assert!((ha[&format!("hu_moment_{i}")] - hb[&format!("hu_moment_{i}")]).abs() < 1e-10);
        }
    }

    #[test]
    fn corrected_fourier_is_translation_invariant() {
        let a = ellipse(100, 100, 45.0, 40.0, 15.0, 24.0);
        let b = ellipse(100, 100, 55.0, 58.0, 15.0, 24.0);
        let fa = fourier(&a.view());
        let fb = fourier(&b.view());
        for i in 0..5 {
            assert!((fa[i] - fb[i]).abs() < 1e-10, "{} {}", fa[i], fb[i]);
        }
    }

    #[test]
    fn hog_ignores_exterior_pixels_and_padding() {
        let mask = ellipse(48, 48, 24.0, 24.0, 12.0, 16.0);
        let base = Array2::from_shape_fn((48, 48), |(r, c)| (r * 3 + c * 5) as f32);
        let changed = Array2::from_shape_fn((48, 48), |index| {
            if mask[index] {
                base[index]
            } else {
                ((index.0 * 97 + index.1 * 53) % 256) as f32
            }
        });
        assert_eq!(
            gradients(&base.view(), &mask.view()),
            gradients(&changed.view(), &mask.view())
        );

        let padded_mask = Array2::from_shape_fn((64, 64), |(r, c)| {
            r >= 8 && c >= 8 && mask.get((r - 8, c - 8)).copied().unwrap_or(false)
        });
        let padded_image = Array2::from_shape_fn((64, 64), |(r, c)| {
            if r >= 8 && c >= 8 {
                base.get((r - 8, c - 8)).copied().unwrap_or(0.0)
            } else {
                0.0
            }
        });
        assert_eq!(
            gradients(&base.view(), &mask.view()),
            gradients(&padded_image.view(), &padded_mask.view())
        );
    }

    #[test]
    fn tiny_nucleus_hog_is_finite_zero() {
        let image = Array2::<f32>::from_elem((5, 5), 42.0);
        let mut mask = Array2::<bool>::from_elem((5, 5), false);
        mask[[2, 2]] = true;
        let result = gradients(&image.view(), &mask.view());
        for value in result.values() {
            assert!(value.is_finite());
        }
        assert_eq!(result["hog_mean"], 0.0);
    }
}
