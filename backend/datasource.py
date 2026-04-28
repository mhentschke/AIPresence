"""Data source abstraction layer.

Defines the DataSource protocol and concrete implementations for
Home Assistant mode and standalone mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from homeassistant_api import Client
from homeassistant_api.errors import EndpointNotFoundError


@dataclass
class EntityState:
    """Normalized entity state returned by any data source."""

    state: str
    attributes: dict[str, Any]


class DataSourceUnavailableError(Exception):
    """Raised when the data source is not available (e.g., standalone mode)."""

    pass


class DataSource(Protocol):
    """Abstract interface for retrieving entity state."""

    def get_entity_state(self, entity_id: str) -> EntityState:
        """Retrieve the current state of an entity by its ID."""
        ...

    def check_entity_exists(self, entity_id: str) -> bool:
        """Check whether an entity ID exists in the data source."""
        ...


class HADataSource:
    """Home Assistant data source using the homeassistant_api library."""

    def __init__(self, ha_url: str, ha_token: str) -> None:
        self.client = Client(ha_url, ha_token)

    def get_entity_state(self, entity_id: str) -> EntityState:
        state = self.client.get_entity(entity_id=entity_id).get_state()
        return EntityState(
            state=state.state,
            attributes=dict(state.attributes),
        )

    def check_entity_exists(self, entity_id: str) -> bool:
        try:
            self.client.get_entity(entity_id=entity_id)
            return True
        except EndpointNotFoundError:
            return False


class StandaloneDataSource:
    """Data source for standalone mode — all operations raise."""

    def get_entity_state(self, entity_id: str) -> EntityState:
        raise DataSourceUnavailableError("Home Assistant is not configured. Live data retrieval is unavailable.")

    def check_entity_exists(self, entity_id: str) -> bool:
        raise DataSourceUnavailableError("Home Assistant is not configured. Entity validation is unavailable.")
