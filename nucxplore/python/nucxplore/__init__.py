from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ._core import (
    __version__,
    check_gpu,
    extract_features as _extract_features,
    extract_features_from_files as _extract_features_from_files,
    get_gpu_device_count,
    save_cropped_nuclei_from_files,
)

_BATCH_ATTRS = frozenset({"BatchExtractor", "batch_extract_features", "batch_extract_and_crop"})


def __getattr__(name: str) -> Any:
    if name in _BATCH_ATTRS:
        from . import batch as _batch

        return getattr(_batch, name)
    raise AttributeError(f"module 'nucxplore' has no attribute {name!r}")


def _iter_crop_masks(masks: Any) -> list[tuple[int, Any]]:
    import numpy as np

    mask_array = np.asarray(masks)
    if mask_array.ndim == 2 and mask_array.dtype == np.bool_:
        return [(1, mask_array)]
    if mask_array.ndim == 2:
        return [
            (int(label), mask_array == label)
            for label in sorted(np.unique(mask_array))
            if int(label) != 0
        ]
    if mask_array.ndim == 3:
        return [
            (index, mask_array[index - 1].astype(bool))
            for index in range(1, mask_array.shape[0] + 1)
        ]
    return [(index, np.asarray(mask, dtype=bool)) for index, mask in enumerate(masks, start=1)]


def extract_features(
    image: Any,
    masks: Any,
    use_gpu: Optional[bool] = None,
    feature_schema: str = "legacy",
    *,
    save_crops: bool = False,
    crop_output_dir: Optional[str | Path] = None,
    padding: int = 10,
) -> list[dict[str, float]]:
    features = _extract_features(
        image, masks, use_gpu=use_gpu, feature_schema=feature_schema,
    )
    if not save_crops:
        return features
    if crop_output_dir is None:
        raise ValueError("crop_output_dir is required when save_crops=True")

    import numpy as np

    from .batch import crop_masked_patch, save_rgb_patch

    image_array = np.asarray(image, dtype=np.uint8)
    output_dir = Path(crop_output_dir) / "nuclei"

    for label, nucleus_mask in _iter_crop_masks(masks):
        patch = crop_masked_patch(image_array, nucleus_mask, padding)
        if patch is not None:
            save_rgb_patch(output_dir / f"nucleus_{label:04d}.png", patch)
    return features


def extract_features_from_files(
    image_path: str | Path,
    mat_path: str | Path,
    *,
    mat_key: Optional[str] = None,
    use_gpu: Optional[bool] = None,
    feature_schema: str = "legacy",
    save_crops: bool = False,
    crop_output_dir: Optional[str | Path] = None,
    padding: int = 10,
) -> list[dict[str, float]]:
    image_path_str = str(Path(image_path))
    mat_path_str = str(Path(mat_path))
    features = _extract_features_from_files(
        image_path_str,
        mat_path_str,
        mat_key=mat_key,
        use_gpu=use_gpu,
        feature_schema=feature_schema,
    )
    if not save_crops:
        return features
    if crop_output_dir is None:
        raise ValueError("crop_output_dir is required when save_crops=True")
    crop_output_dir_str = str(Path(crop_output_dir))
    save_cropped_nuclei_from_files(
        image_path=image_path_str,
        mat_path=mat_path_str,
        output_dir=crop_output_dir_str,
        mat_key=mat_key,
        padding=padding,
    )
    return features


__all__ = [
    "__version__",
    "extract_features",
    "extract_features_from_files",
    "save_cropped_nuclei_from_files",
    "BatchExtractor",
    "batch_extract_features",
    "batch_extract_and_crop",
    "check_gpu",
    "get_gpu_device_count",
]
