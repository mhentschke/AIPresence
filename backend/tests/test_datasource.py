"""Unit tests for the data source abstraction layer."""

from unittest.mock import MagicMock, patch

import pytest

from backend.datasource import (
    DataSourceUnavailableError,
    EntityState,
    HADataSource,
    StandaloneDataSource,
)


# ---------------------------------------------------------------------------
# HADataSource
# ---------------------------------------------------------------------------

class TestHADataSource:
    def test_get_entity_state_returns_entity_state(self):
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {"friendly_name": "Motion", "device_class": "motion"}

        mock_entity = MagicMock()
        mock_entity.get_state.return_value = mock_state

        with patch("backend.datasource.Client") as MockClient:
            MockClient.return_value.get_entity.return_value = mock_entity
            ds = HADataSource("http://ha:8123", "token123")
            result = ds.get_entity_state("binary_sensor.motion")

        assert isinstance(result, EntityState)
        assert result.state == "on"
        assert result.attributes == {"friendly_name": "Motion", "device_class": "motion"}

    def test_check_entity_exists_true(self):
        with patch("backend.datasource.Client") as MockClient:
            MockClient.return_value.get_entity.return_value = MagicMock()
            ds = HADataSource("http://ha:8123", "token123")
            assert ds.check_entity_exists("binary_sensor.motion") is True

    def test_check_entity_exists_false(self):
        from homeassistant_api.errors import EndpointNotFoundError

        with patch("backend.datasource.Client") as MockClient:
            MockClient.return_value.get_entity.side_effect = EndpointNotFoundError("not found")
            ds = HADataSource("http://ha:8123", "token123")
            assert ds.check_entity_exists("binary_sensor.missing") is False


# ---------------------------------------------------------------------------
# StandaloneDataSource
# ---------------------------------------------------------------------------

class TestStandaloneDataSource:
    def test_get_entity_state_raises(self):
        ds = StandaloneDataSource()
        with pytest.raises(DataSourceUnavailableError):
            ds.get_entity_state("binary_sensor.motion")

    def test_check_entity_exists_raises(self):
        ds = StandaloneDataSource()
        with pytest.raises(DataSourceUnavailableError):
            ds.check_entity_exists("binary_sensor.motion")
