"""Unit tests for the ML pipeline: data preparation, scaling, and training."""

import numpy as np
import pandas as pd
import pytest

from backend.classes import Model, Model_Stats, append_to_dataframe


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _synthetic_df(n_per_room=20):
    """Build a small synthetic DataFrame with 3 rooms and 4 sensor columns."""
    rooms = ["kitchen", "office", "bedroom"]
    rows = []
    rng = np.random.RandomState(42)
    for room in rooms:
        for _ in range(n_per_room):
            rows.append({
                "room": room,
                "sensor_a": rng.rand(),
                "sensor_b": rng.rand(),
                "sensor_c": rng.rand(),
                "sensor_d": rng.rand(),
            })
    return pd.DataFrame(rows)


@pytest.fixture()
def model():
    """A Model instance with no disk path needed (tests don't persist)."""
    m = Model(data_path="/tmp/test_model")
    m.data = _synthetic_df()
    return m


# ---------------------------------------------------------------------------
# data_prep
# ---------------------------------------------------------------------------

class TestDataPrep:
    def test_produces_correct_x_and_y_shapes(self, model):
        X, Y = model.data_prep(model.data.copy(deep=True))
        # Y should have one column per room
        assert set(Y.columns) == {"room_kitchen", "room_office", "room_bedroom"}
        # X should have only sensor columns, no room-related columns
        assert all(not c.startswith("room") for c in X.columns)
        # Row counts should match
        assert len(X) == len(Y)

    def test_y_is_one_hot(self, model):
        _, Y = model.data_prep(model.data.copy(deep=True))
        # Each row should have exactly one 1
        assert (Y.sum(axis=1) == 1).all()

    def test_x_contains_sensor_columns(self, model):
        X, _ = model.data_prep(model.data.copy(deep=True))
        for col in ["sensor_a", "sensor_b", "sensor_c", "sensor_d"]:
            assert col in X.columns


# ---------------------------------------------------------------------------
# data_prep_prediction
# ---------------------------------------------------------------------------

class TestDataPrepPrediction:
    def test_drops_extra_columns(self, model):
        pred_df = pd.DataFrame({
            "sensor_a": [0.5],
            "sensor_b": [0.3],
            "sensor_c": [0.2],
            "sensor_d": [0.1],
            "extra_col": [999],
        })
        result = model.data_prep_prediction(pred_df)
        assert "extra_col" not in result.columns

    def test_fills_missing_columns_with_zero(self, model):
        # Only provide a subset of sensor columns
        pred_df = pd.DataFrame({"sensor_a": [0.5]})
        result = model.data_prep_prediction(pred_df)
        assert "sensor_b" in result.columns
        assert result["sensor_b"].iloc[0] == 0

    def test_drops_room_column(self, model):
        pred_df = pd.DataFrame({
            "room": ["kitchen"],
            "sensor_a": [0.5],
            "sensor_b": [0.3],
            "sensor_c": [0.2],
            "sensor_d": [0.1],
        })
        result = model.data_prep_prediction(pred_df)
        assert "room" not in result.columns


# ---------------------------------------------------------------------------
# append_to_dataframe
# ---------------------------------------------------------------------------

class TestAppendToDataframe:
    def test_include_new_columns_true(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        result = append_to_dataframe(df, {"a": 3, "b": 4, "c": 5}, include_new_columns=True)
        assert "c" in result.columns
        assert len(result) == 2

    def test_include_new_columns_false(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        result = append_to_dataframe(df, {"a": 3, "b": 4, "c": 5}, include_new_columns=False)
        assert "c" not in result.columns
        assert len(result) == 2


# ---------------------------------------------------------------------------
# apply_scaler
# ---------------------------------------------------------------------------

class TestApplyScaler:
    def test_fit_true_creates_scaler(self, model):
        X, _ = model.data_prep(model.data.copy(deep=True))
        assert model.scaler is None
        model.apply_scaler(X, fit=True)
        assert model.scaler is not None

    def test_fit_true_scales_data(self, model):
        X, _ = model.data_prep(model.data.copy(deep=True))
        scaled = model.apply_scaler(X, fit=True)
        assert scaled.min().min() >= -1e-9  # approximately >= 0
        assert scaled.max().max() <= 1.0 + 1e-9  # approximately <= 1

    def test_fit_false_uses_existing_scaler(self, model):
        X, _ = model.data_prep(model.data.copy(deep=True))
        model.apply_scaler(X, fit=True)
        scaler_before = model.scaler
        model.apply_scaler(X, fit=False)
        assert model.scaler is scaler_before


# ---------------------------------------------------------------------------
# train
# ---------------------------------------------------------------------------

class TestTrain:
    def test_returns_model_and_stats(self, model):
        trained_model, stats = model.train()
        assert trained_model is not None
        assert isinstance(stats, Model_Stats)

    def test_stats_fields_populated(self, model):
        _, stats = model.train()
        assert stats.accuracy > 0
        assert stats.model_type != ""
        assert stats.classification_report is not None
        assert len(stats.classification_report) > 0
