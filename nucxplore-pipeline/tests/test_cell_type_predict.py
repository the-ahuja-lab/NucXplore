from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

class MockBooster:
    def __init__(self, feature_names: list[str]) -> None:
        self.feature_names = feature_names


class MockModel:
    def __init__(self, feature_names: list[str]) -> None:
        self._feature_names = feature_names

    def get_booster(self) -> MockBooster:
        return MockBooster(self._feature_names)

    def predict(self, x):
        return [0 for _ in range(len(x))]

    def predict_proba(self, x):
        return [[0.9, 0.1] for _ in range(len(x))]


class MockEncoder:
    def inverse_transform(self, indices):
        return ["CellA" if int(i) == 0 else "CellB" for i in indices]


def load_predict_module():
    script = Path(__file__).resolve().parents[1] / "bin" / "cell_type_predict.py"
    spec = importlib.util.spec_from_file_location("cell_type_predict_module", script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_predictor_success(tmp_path: Path) -> None:
    module = load_predict_module()
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir(parents=True)

    df = pd.DataFrame({"f1": [1.0, 2.0], "f2": [3.0, 4.0], "nucleus_id": [1, 2]})
    input_csv = input_dir / "sample.csv"
    df.to_csv(input_csv, index=False)

    out_csv = output_dir / "sample.csv"
    result = module.process_csv(
        input_csv=input_csv,
        output_csv=out_csv,
        model=MockModel(["f1", "f2"]),
        encoder=MockEncoder(),
        feature_names=["f1", "f2"],
    )
    assert result.status == "ok"
    assert out_csv.exists()
    out_df = pd.read_csv(out_csv)
    assert "Predicted_Label" in out_df.columns
    assert "Confidence_Score" in out_df.columns
    assert list(out_df["Predicted_Label"]) == ["CellA", "CellA"]


def test_predictor_fails_on_missing_features(tmp_path: Path) -> None:
    module = load_predict_module()
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir(parents=True)

    df = pd.DataFrame({"f1": [1.0], "nucleus_id": [1]})
    input_csv = input_dir / "bad.csv"
    df.to_csv(input_csv, index=False)

    result = module.process_csv(
        input_csv=input_csv,
        output_csv=output_dir / "bad.csv",
        model=MockModel(["f1", "f2"]),
        encoder=MockEncoder(),
        feature_names=["f1", "f2"],
    )
    assert result.status == "failed_missing_features"
    assert result.error is not None
    assert "Missing" in result.error
    assert "bad.csv" in result.error
