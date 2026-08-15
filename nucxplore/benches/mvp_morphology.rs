use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use ndarray::Array2;
use nucxplore::features::extract_morphology_batch;
use nucxplore::features::morphology::calculate_morphological_features;

fn generate_masks(mask_count: usize, side: usize) -> Vec<Array2<bool>> {
    let mut masks = Vec::with_capacity(mask_count);
    for i in 0..mask_count {
        let mut mask = Array2::from_elem((side, side), false);
        let offset = (i * 7) % (side.saturating_sub(12).max(1));
        for r in (offset + 2)..(offset + 10).min(side) {
            for c in (offset + 2)..(offset + 10).min(side) {
                mask[[r, c]] = true;
            }
        }
        masks.push(mask);
    }
    masks
}

fn extract_morphology_sequential(
    masks: &[Array2<bool>],
) -> Vec<std::collections::HashMap<String, f64>> {
    masks
        .iter()
        .map(|mask| {
            let tuples = calculate_morphological_features(&mask.view()).unwrap();
            tuples.into_iter().collect()
        })
        .collect()
}

fn bench_phase2_morphology(c: &mut Criterion) {
    let mut group = c.benchmark_group("phase2_morphology");
    let image_shape = (64, 64, 3);
    let test_sizes = [32_usize, 64, 128, 256, 512, 2048];

    for mask_count in test_sizes {
        let masks = generate_masks(mask_count, 64);
        group.bench_with_input(
            BenchmarkId::new("rust_seq", mask_count),
            &mask_count,
            |b, _| b.iter(|| extract_morphology_sequential(black_box(&masks))),
        );
        group.bench_with_input(
            BenchmarkId::new("rust_rayon", mask_count),
            &mask_count,
            |b, _| {
                b.iter(|| extract_morphology_batch(image_shape, black_box(&masks), false).unwrap())
            },
        );
    }

    group.finish();
}

fn bench_morphology_side_scaling(c: &mut Criterion) {
    let mut group = c.benchmark_group("morphology_side_scaling");
    let mask_count = 128;

    for side in [32_usize, 64, 128, 256] {
        let masks = generate_masks(mask_count, side);
        let image_shape = (side, side, 3);
        group.bench_with_input(BenchmarkId::new("seq", side), &side, |b, _| {
            b.iter(|| extract_morphology_sequential(black_box(&masks)))
        });
        group.bench_with_input(BenchmarkId::new("rayon", side), &side, |b, _| {
            b.iter(|| extract_morphology_batch(image_shape, black_box(&masks), false).unwrap())
        });
    }

    group.finish();
}

criterion_group!(
    benches,
    bench_phase2_morphology,
    bench_morphology_side_scaling
);
criterion_main!(benches);
