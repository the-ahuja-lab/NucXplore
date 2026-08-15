from __future__ import annotations

import argparse
import csv
import json
import os
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np

from ._core import extract_features
from .io import load_instance_map, load_rgb_image

DEFAULT_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")
DEFAULT_METADATA_COLS = (
    "Tissue",
    "Sex",
    "Age Bracket",
    "Hardy Scale",
    "Pathology Categories",
)
DEFAULT_METADATA_KEY_COLUMN = "Tissue Sample ID"
DEFAULT_INST_TYPE_KEY = "inst_type"

MORPHOLOGY_COLUMNS = [
    "area",
    "perimeter",
    "equivalent_diameter",
    "major_axis_length",
    "minor_axis_length",
    "eccentricity",
    "solidity",
    "extent",
    "convex_area",
    "euler_number",
    "orientation",
    "centroid_row",
    "centroid_col",
    "circularity",
    "aspect_ratio",
    "hu_moment_1",
    "hu_moment_2",
    "hu_moment_3",
    "hu_moment_4",
    "hu_moment_5",
    "hu_moment_6",
    "hu_moment_7",
]
ADVANCED_SHAPE_COLUMNS = [
    "convexity",
    "fractal_dimension",
    "roughness",
    "bending_energy",
    "fourier_descriptor_1",
    "fourier_descriptor_2",
    "fourier_descriptor_3",
    "fourier_descriptor_4",
    "fourier_descriptor_5",
]
NEIS_COLUMNS = [
    "neis_irregularity_score",
    "neis_spectral_energy",
    "neis_spectral_peak_mode",
]
PATCH_FEATURE_COLUMNS = [
    "mean_intensity",
    "median_intensity",
    "std_intensity",
    "min_intensity",
    "max_intensity",
    "range_intensity",
    "iqr_intensity",
    "skewness_intensity",
    "kurtosis_intensity",
    "entropy_intensity",
    "glcm_contrast",
    "glcm_dissimilarity",
    "glcm_homogeneity",
    "glcm_energy",
    "glcm_correlation",
    "glcm_ASM",
    "lbp_mean",
    "lbp_std",
    "lbp_entropy",
    "mean_hematoxylin",
    "std_hematoxylin",
    "skew_hematoxylin",
    "kurt_hematoxylin",
    "min_hematoxylin",
    "max_hematoxylin",
    "mean_eosin",
    "std_eosin",
    "skew_eosin",
    "kurt_eosin",
    "min_eosin",
    "max_eosin",
    "he_ratio_H_to_E",
    "hog_mean",
    "hog_std",
    "hog_max",
    "hog_min",
    "ccsm_condensed_area_ratio",
    "ccsm_num_clumps",
    "ccsm_mean_clump_area",
    "ccsm_mean_clump_eccentricity",
    "ccsm_mean_clump_solidity",
    "ccsm_mean_dist_to_boundary",
    "ccsm_mean_nnd",
    "ccsm_contrast",
    "ccsm_correlation",
    "ccsm_energy",
    "ccsm_homogeneity",
]

V2_ADDITIONAL_COLUMNS = [
    "fractal_dimension_r2",
    "fractal_dimension_scales",
    "he_deconvolution_valid",
    "boundary_gradient_mean",
    "boundary_gradient_std",
    "boundary_gradient_max",
    "boundary_orientation_entropy",
]
V2_FEATURE_COLUMNS = [
    *(f"v2_{name}" for name in MORPHOLOGY_COLUMNS),
    *(f"v2_{name}" for name in ADVANCED_SHAPE_COLUMNS),
    "v2_fractal_dimension_r2",
    "v2_fractal_dimension_scales",
    *(f"v2_{name}" for name in NEIS_COLUMNS),
    *(f"v2_{name}" for name in PATCH_FEATURE_COLUMNS),
    "v2_he_deconvolution_valid",
    "v2_boundary_gradient_mean",
    "v2_boundary_gradient_std",
    "v2_boundary_gradient_max",
    "v2_boundary_orientation_entropy",
    "v2_distance_to_nearest_neighbor",
]
assert len(V2_FEATURE_COLUMNS) == 89 and len(set(V2_FEATURE_COLUMNS)) == 89


@dataclass(frozen=True)
class BatchTask:
    image_path: str
    mat_path: str
    csv_output_path: str
    nuclei_output_dir: str
    metadata_features: dict[str, str]
    metadata_columns: tuple[str, ...]
    mat_key: Optional[str]
    inst_type_key: str
    padding: int
    use_gpu: bool
    feature_schema: str
    save_crops: bool


@dataclass(frozen=True)
class ImageResult:
    ok: bool
    image_path: str
    mat_path: Optional[str]
    mat_key: Optional[str]
    nuclei: int
    warnings: tuple[str, ...] = ()
    error: Optional[str] = None
    traceback: Optional[str] = None


@dataclass(frozen=True)
class BatchResult:
    tasks_discovered: int
    completed_images: int
    failed_images: int
    total_nuclei: int
    warnings: list[str]
    results: list[ImageResult]


def _split_csv_arg(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def iter_image_paths(root: Path, extensions: Sequence[str], recursive: bool) -> list[Path]:
    extension_set = {ext.lower() for ext in extensions}
    walker = root.rglob("*") if recursive else root.glob("*")
    image_paths = [
        path for path in walker if path.is_file() and path.suffix.lower() in extension_set
    ]
    image_paths.sort(key=lambda path: str(path.relative_to(root)))
    return image_paths


def derive_metadata_id(relative_image_path: Path, mode: str) -> str:
    if mode == "first_dir":
        if len(relative_image_path.parts) > 1:
            return relative_image_path.parts[0]
        return relative_image_path.stem
    if mode == "parent_dir":
        return relative_image_path.parent.name or relative_image_path.stem
    return relative_image_path.stem


def load_metadata(
    metadata_csv: Optional[Path],
    key_column: str,
    metadata_columns: Sequence[str],
) -> dict[str, dict[str, str]]:
    if metadata_csv is None:
        return {}
    with metadata_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Metadata CSV has no header: {metadata_csv}")
        missing = [col for col in [key_column, *metadata_columns] if col not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"Metadata CSV is missing required columns: {', '.join(missing)}"
            )
        metadata_by_id: dict[str, dict[str, str]] = {}
        for row in reader:
            key = (row.get(key_column) or "").strip()
            if not key:
                continue
            metadata_by_id[key] = {
                col: (row.get(col) or "").strip() for col in metadata_columns
            }
    return metadata_by_id


def build_tasks(
    image_root: Path,
    mat_root: Path,
    output_csv_root: Path,
    output_nuclei_root: Path,
    image_extensions: Sequence[str],
    recursive: bool,
    max_images: Optional[int],
    skip_existing: bool,
    metadata_by_id: dict[str, dict[str, str]],
    metadata_columns: Sequence[str],
    metadata_id_source: str,
    mat_key: Optional[str],
    inst_type_key: str,
    padding: int,
    use_gpu: bool,
    feature_schema: str,
    save_crops: bool,
) -> tuple[list[BatchTask], list[str]]:
    warnings: list[str] = []
    tasks: list[BatchTask] = []
    for image_path in iter_image_paths(image_root, image_extensions, recursive):
        relative_path = image_path.relative_to(image_root)
        mat_path = (mat_root / relative_path).with_suffix(".mat")
        if not mat_path.exists():
            warnings.append(f"Missing MAT pair for {relative_path}")
            continue

        csv_output_path = (output_csv_root / relative_path).with_suffix(".csv")
        nuclei_output_dir = output_nuclei_root / relative_path.with_suffix("")
        if skip_existing and csv_output_path.exists():
            continue

        metadata_id = derive_metadata_id(relative_path, metadata_id_source)
        metadata_features = metadata_by_id.get(metadata_id, {})
        if metadata_by_id and not metadata_features:
            warnings.append(
                f"No metadata match for {relative_path} using key '{metadata_id}'"
            )

        tasks.append(
            BatchTask(
                image_path=str(image_path),
                mat_path=str(mat_path),
                csv_output_path=str(csv_output_path),
                nuclei_output_dir=str(nuclei_output_dir),
                metadata_features=dict(metadata_features),
                metadata_columns=tuple(metadata_columns),
                mat_key=mat_key,
                inst_type_key=inst_type_key,
                padding=padding,
                use_gpu=use_gpu,
                feature_schema=feature_schema,
                save_crops=save_crops,
            )
        )
        if max_images is not None and len(tasks) >= max_images:
            break
    return tasks, warnings


def _unwrap_mat_scalar(value: Any) -> Any:
    current = value
    while isinstance(current, np.ndarray):
        if current.size == 0:
            return ""
        if current.ndim == 0:
            current = current.item()
            continue
        if current.size == 1:
            current = current.reshape(-1)[0]
            continue
        break
    if isinstance(current, bytes):
        return current.decode("utf-8", errors="ignore")
    if hasattr(current, "item") and not isinstance(current, str):
        try:
            return current.item()
        except Exception:
            return current
    return current


def load_instance_types(mat_path: Path, inst_type_key: str) -> tuple[dict[int, str], Optional[str]]:
    try:
        from scipy.io import loadmat
    except ImportError:
        return {}, f"scipy unavailable; using Unknown nucleus_type for {mat_path.name}"
    mat_data = loadmat(mat_path)
    raw = mat_data.get(inst_type_key)
    if raw is None:
        return {}, f"inst_type key '{inst_type_key}' missing in {mat_path.name}; using Unknown nucleus_type"
    flat = np.asarray(raw, dtype=object).reshape(-1)
    instance_types: dict[int, str] = {}
    for index, value in enumerate(flat, start=1):
        parsed = _unwrap_mat_scalar(value)
        instance_types[index] = str(parsed).strip()
    return instance_types, None


def crop_masked_patch(
    image: np.ndarray,
    nucleus_mask: np.ndarray,
    padding: int,
) -> Optional[np.ndarray]:
    coords = np.argwhere(nucleus_mask)
    if coords.size == 0:
        return None

    min_row, min_col = coords.min(axis=0)
    max_row, max_col = coords.max(axis=0)
    image_h, image_w = image.shape[:2]

    min_row = max(0, int(min_row) - padding)
    min_col = max(0, int(min_col) - padding)
    max_row = min(image_h - 1, int(max_row) + padding)
    max_col = min(image_w - 1, int(max_col) + padding)

    cropped_image = image[min_row : max_row + 1, min_col : max_col + 1].copy()
    cropped_mask = nucleus_mask[min_row : max_row + 1, min_col : max_col + 1]
    return cropped_image * cropped_mask[..., np.newaxis].astype(cropped_image.dtype)


def save_rgb_patch(path: Path, patch: np.ndarray) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.asarray(patch, dtype=np.uint8), mode="RGB").save(path)


def coerce_feature_value(value: Any) -> Any:
    scalar = _unwrap_mat_scalar(value)
    if isinstance(scalar, (float, np.floating)):
        if not np.isfinite(float(scalar)):
            return 0.0
        return float(scalar)
    if isinstance(scalar, (int, np.integer)):
        return int(scalar)
    return scalar


def legacy_fieldnames(
    metadata_columns: Sequence[str], rows: Sequence[dict[str, Any]]
) -> list[str]:
    ordered = ["nucleus_id", *metadata_columns, "nucleus_type"]
    ordered.extend(MORPHOLOGY_COLUMNS)
    ordered.extend(ADVANCED_SHAPE_COLUMNS)
    ordered.extend(NEIS_COLUMNS)
    for prefix in ("pre_norm_", "post_norm_"):
        ordered.extend(f"{prefix}{name}" for name in PATCH_FEATURE_COLUMNS)
    ordered.append("distance_to_nearest_neighbor")

    ordered.extend(V2_FEATURE_COLUMNS if any(
        any(key.startswith("v2_") for key in row) for row in rows
    ) else [])
    seen = set(ordered)
    extras: set[str] = set()
    for row in rows:
        extras.update(key for key in row.keys() if key not in seen)
    ordered.extend(sorted(extras))
    return ordered


def write_csv(path: Path, rows: Sequence[dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def process_single_task(task: BatchTask) -> ImageResult:
    try:
        local_warnings: list[str] = []
        image_path = Path(task.image_path)
        mat_path = Path(task.mat_path)
        instance_map, detected_key = load_instance_map(mat_path, preferred_key=task.mat_key)
        image = load_rgb_image(image_path)
        features = extract_features(
            image,
            instance_map.astype(np.uint32, copy=False),
            use_gpu=task.use_gpu,
            feature_schema=task.feature_schema,
        )
        instance_types, instance_type_warning = load_instance_types(mat_path, task.inst_type_key)
        if instance_type_warning:
            local_warnings.append(instance_type_warning)

        rows: list[dict[str, Any]] = []
        for feature_row in features:
            nucleus_id = int(round(float(feature_row.get("nucleus_id", 0))))
            row: dict[str, Any] = {"nucleus_id": nucleus_id}
            for column in task.metadata_columns:
                row[column] = task.metadata_features.get(column, "")
            row["nucleus_type"] = instance_types.get(nucleus_id, "Unknown")
            for key, value in feature_row.items():
                if key == "nucleus_id":
                    continue
                row[key] = coerce_feature_value(value)
            rows.append(row)

        if rows:
            if task.feature_schema == "v2":
                fieldnames = ["nucleus_id", *task.metadata_columns, "nucleus_type"]
                fieldnames.extend(V2_FEATURE_COLUMNS)
            else:
                fieldnames = legacy_fieldnames(task.metadata_columns, rows)
            write_csv(Path(task.csv_output_path), rows, fieldnames)
            Path(f"{task.csv_output_path}.schema.json").write_text(
                json.dumps({"feature_schema": task.feature_schema,
                            "schema_version": 2 if task.feature_schema in ("dual", "v2") else 1,
                            "algorithm_revision": "v3.0",
                            "feature_count": {"legacy": 129, "dual": 218, "v2": 89}[task.feature_schema],
                            "stain_normalization": True,
                            "padding": task.padding}, indent=2) + "\n",
                encoding="utf-8",
            )
            if task.save_crops:
                labels = sorted(int(label) for label in np.unique(instance_map) if int(label) != 0)
                crop_dir = Path(task.nuclei_output_dir) / "nuclei"
                for label in labels:
                    nucleus_mask = instance_map == label
                    patch = crop_masked_patch(image, nucleus_mask, task.padding)
                    if patch is not None:
                        save_rgb_patch(crop_dir / f"nucleus_{label:04d}.png", patch)

        return ImageResult(
            ok=True,
            image_path=str(image_path),
            mat_path=str(mat_path),
            mat_key=detected_key,
            nuclei=len(rows),
            warnings=tuple(local_warnings),
        )
    except Exception as exc:
        return ImageResult(
            ok=False,
            image_path=task.image_path,
            mat_path=task.mat_path,
            mat_key=None,
            nuclei=0,
            error=str(exc),
            traceback=traceback.format_exc(),
        )


def run_tasks(tasks: Sequence[BatchTask], workers: int) -> list[ImageResult]:
    if workers <= 1:
        return [process_single_task(task) for task in tasks]
    results: list[ImageResult] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_single_task, task): task for task in tasks}
        for future in as_completed(futures):
            results.append(future.result())
    return results


class BatchExtractor:
    def __init__(
        self,
        image_root: Path | str,
        mat_root: Path | str,
        output_csv_root: Path | str,
        output_nuclei_root: Path | str,
        *,
        image_exts: Sequence[str] = DEFAULT_IMAGE_EXTS,
        recursive: bool = True,
        workers: Optional[int] = None,
        max_images: Optional[int] = None,
        skip_existing: bool = False,
        mat_key: Optional[str] = None,
        inst_type_key: str = DEFAULT_INST_TYPE_KEY,
        padding: int = 10,
        use_gpu: bool = False,
        feature_schema: str = "legacy",
        metadata_csv: Optional[Path | str] = None,
        metadata_key_column: str = DEFAULT_METADATA_KEY_COLUMN,
        metadata_cols: Sequence[str] = DEFAULT_METADATA_COLS,
        metadata_id_source: str = "first_dir",
    ) -> None:
        self.image_root = Path(image_root).expanduser().resolve()
        self.mat_root = Path(mat_root).expanduser().resolve()
        self.output_csv_root = Path(output_csv_root).expanduser().resolve()
        self.output_nuclei_root = Path(output_nuclei_root).expanduser().resolve()
        self.image_exts = tuple(image_exts)
        self.recursive = recursive
        self.workers = workers if workers is not None else max(1, (os.cpu_count() or 1) - 1)
        self.max_images = max_images
        self.skip_existing = skip_existing
        self.mat_key = mat_key
        self.inst_type_key = inst_type_key
        self.padding = padding
        self.use_gpu = use_gpu
        if feature_schema not in {"legacy", "dual", "v2"}:
            raise ValueError("feature_schema must be legacy, dual, or v2")
        self.feature_schema = feature_schema
        self.metadata_csv = Path(metadata_csv).expanduser().resolve() if metadata_csv else None
        self.metadata_key_column = metadata_key_column
        self.metadata_cols = tuple(metadata_cols)
        self.metadata_id_source = metadata_id_source

    def extract(
        self,
        *,
        save_crops: bool = False,
    ) -> BatchResult:
        metadata_by_id = load_metadata(
            self.metadata_csv, self.metadata_key_column, self.metadata_cols
        )
        tasks, warnings = build_tasks(
            image_root=self.image_root,
            mat_root=self.mat_root,
            output_csv_root=self.output_csv_root,
            output_nuclei_root=self.output_nuclei_root,
            image_extensions=self.image_exts,
            recursive=self.recursive,
            max_images=self.max_images,
            skip_existing=self.skip_existing,
            metadata_by_id=metadata_by_id,
            metadata_columns=self.metadata_cols,
            metadata_id_source=self.metadata_id_source,
            mat_key=self.mat_key,
            inst_type_key=self.inst_type_key,
            padding=self.padding,
            use_gpu=self.use_gpu,
            feature_schema=self.feature_schema,
            save_crops=save_crops,
        )
        results = run_tasks(tasks, self.workers)
        warnings_out = list(warnings)
        for result in results:
            warnings_out.extend(result.warnings)
        completed = sum(1 for result in results if result.ok)
        failed = len(results) - completed
        total_nuclei = sum(result.nuclei for result in results if result.ok)
        return BatchResult(
            tasks_discovered=len(tasks),
            completed_images=completed,
            failed_images=failed,
            total_nuclei=total_nuclei,
            warnings=warnings_out,
            results=results,
        )

    def extract_features(
        self,
        *,
        save_crops: bool = False,
    ) -> BatchResult:
        return self.extract(save_crops=save_crops)

    def extract_and_crop(self) -> BatchResult:
        return self.extract(save_crops=True)


def batch_extract_features(
    image_root: Path | str,
    mat_root: Path | str,
    output_csv_root: Path | str,
    output_nuclei_root: Path | str,
    *,
    save_crops: bool = False,
    **kwargs: Any,
) -> BatchResult:
    extractor = BatchExtractor(
        image_root=image_root,
        mat_root=mat_root,
        output_csv_root=output_csv_root,
        output_nuclei_root=output_nuclei_root,
        **kwargs,
    )
    return extractor.extract_features(save_crops=save_crops)


def batch_extract_and_crop(
    image_root: Path | str,
    mat_root: Path | str,
    output_csv_root: Path | str,
    output_nuclei_root: Path | str,
    *,
    image_exts: Sequence[str] = DEFAULT_IMAGE_EXTS,
    recursive: bool = True,
    workers: Optional[int] = None,
    max_images: Optional[int] = None,
    skip_existing: bool = False,
    mat_key: Optional[str] = None,
    inst_type_key: str = DEFAULT_INST_TYPE_KEY,
    padding: int = 10,
    use_gpu: bool = False,
    feature_schema: str = "legacy",
    metadata_csv: Optional[Path | str] = None,
    metadata_key_column: str = DEFAULT_METADATA_KEY_COLUMN,
    metadata_cols: Sequence[str] = DEFAULT_METADATA_COLS,
    metadata_id_source: str = "first_dir",
    save_crops: bool = True,
) -> BatchResult:
    extractor = BatchExtractor(
        image_root=image_root,
        mat_root=mat_root,
        output_csv_root=output_csv_root,
        output_nuclei_root=output_nuclei_root,
        image_exts=image_exts,
        recursive=recursive,
        workers=workers,
        max_images=max_images,
        skip_existing=skip_existing,
        mat_key=mat_key,
        inst_type_key=inst_type_key,
        padding=padding,
        use_gpu=use_gpu,
        feature_schema=feature_schema,
        metadata_csv=metadata_csv,
        metadata_key_column=metadata_key_column,
        metadata_cols=metadata_cols,
        metadata_id_source=metadata_id_source,
    )
    return extractor.extract(save_crops=save_crops)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch feature extraction for paired image and .mat files."
    )
    parser.add_argument("--image-root", type=Path, required=True, help="Input image root")
    parser.add_argument("--mat-root", type=Path, required=True, help="Input .mat root")
    parser.add_argument(
        "--output-csv-root",
        type=Path,
        required=True,
        help="Root directory for per-image CSV outputs",
    )
    parser.add_argument(
        "--output-nuclei-root",
        type=Path,
        required=True,
        help="Root directory for cropped nucleus outputs",
    )
    parser.add_argument(
        "--image-exts",
        type=str,
        default=",".join(DEFAULT_IMAGE_EXTS),
        help="Comma-separated image extensions to scan",
    )
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Recursively scan the image root",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, (os.cpu_count() or 1) - 1),
        help="Number of worker processes",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Optional cap on number of paired images to process",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip images whose CSV output already exists",
    )
    parser.add_argument(
        "--mat-key",
        type=str,
        default=None,
        help="Specific instance-map key inside the .mat file",
    )
    parser.add_argument(
        "--inst-type-key",
        type=str,
        default=DEFAULT_INST_TYPE_KEY,
        help="Optional nucleus-type key inside the .mat file",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=10,
        help="Padding used for cropped nucleus patches",
    )
    parser.add_argument(
        "--use-gpu",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Use GPU for nucxplore extraction",
    )
    parser.add_argument(
        "--metadata-csv",
        type=Path,
        default=None,
        help="Optional metadata CSV to append per nucleus",
    )
    parser.add_argument(
        "--feature-schema", choices=("legacy", "dual", "v2"), default="legacy"
    )
    parser.add_argument(
        "--metadata-key-column",
        type=str,
        default=DEFAULT_METADATA_KEY_COLUMN,
        help="Key column in metadata CSV",
    )
    parser.add_argument(
        "--metadata-cols",
        type=str,
        default=",".join(DEFAULT_METADATA_COLS),
        help="Comma-separated metadata columns to copy into the output CSV",
    )
    parser.add_argument(
        "--metadata-id-source",
        choices=("first_dir", "parent_dir", "stem"),
        default="first_dir",
        help="How to derive the metadata key from each image path",
    )
    parser.add_argument(
        "--save-crops",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save cropped nuclei images alongside CSV extraction",
    )
    return parser.parse_args()


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ = argv
    args = parse_args()
    metadata_columns = tuple(_split_csv_arg(args.metadata_cols)) if args.metadata_csv else tuple()
    image_extensions = tuple(_split_csv_arg(args.image_exts))
    try:
        result = batch_extract_and_crop(
            image_root=args.image_root,
            mat_root=args.mat_root,
            output_csv_root=args.output_csv_root,
            output_nuclei_root=args.output_nuclei_root,
            image_exts=image_extensions,
            recursive=args.recursive,
            workers=args.workers,
            max_images=args.max_images,
            skip_existing=args.skip_existing,
            mat_key=args.mat_key,
            inst_type_key=args.inst_type_key,
            padding=args.padding,
            use_gpu=args.use_gpu,
            feature_schema=args.feature_schema,
            metadata_csv=args.metadata_csv,
            metadata_key_column=args.metadata_key_column,
            metadata_cols=metadata_columns,
            metadata_id_source=args.metadata_id_source,
            save_crops=args.save_crops,
        )
    except Exception as exc:
        print(f"Failed to prepare tasks: {exc}")
        return 1

    for warning in result.warnings:
        print(f"WARN {warning}")

    if result.tasks_discovered == 0:
        print("No paired image/.mat files found.")
        return 1

    print(f"Discovered {result.tasks_discovered} paired image/.mat tasks.")
    print(f"Workers: {args.workers}")
    print(f"GPU enabled: {args.use_gpu}")

    for item in result.results:
        image_name = Path(item.image_path).name
        if item.ok:
            print(f"OK  {image_name} | nuclei={item.nuclei} | mat_key={item.mat_key}")
        else:
            print(f"ERR {image_name} | {item.error}")

    print("")
    print(f"Completed images: {result.completed_images}")
    print(f"Failed images: {result.failed_images}")
    print(f"Total nuclei saved: {result.total_nuclei}")

    if result.failed_images:
        print("")
        print("Error details:")
        for item in result.results:
            if not item.ok:
                print(f"- {item.image_path}")
                if item.traceback:
                    print(item.traceback)
        return 1
    return 0
