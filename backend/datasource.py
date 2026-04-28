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

    def list_entities(self, domain: str | None = None) -> list[dict[str, str]]:
        """List available entities, optionally filtered by domain."""
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

    def list_entities(self, domain: str | None = None) -> list[dict[str, str]]:
        groups = self.client.get_entities()
        result: list[dict[str, str]] = []
        domains = [domain] if domain else list(vars(groups).keys())
        for d in domains:
            group = getattr(groups, d, None)
            if group is None:
                continue
            for eid, entity in group.entities.items():
                state = entity.get_state()
                friendly = state.attributes.get("friendly_name", eid) if state and state.attributes else eid
                result.append({"entity_id": eid, "friendly_name": friendly})
        return result


class StandaloneDataSource:
    """Data source for standalone mode — all operations raise."""

    def get_entity_state(self, entity_id: str) -> EntityState:
        raise DataSourceUnavailableError("Home Assistant is not configured. Live data retrieval is unavailable.")

    def check_entity_exists(self, entity_id: str) -> bool:
        raise DataSourceUnavailableError("Home Assistant is not configured. Entity validation is unavailable.")

    def list_entities(self, domain: str | None = None) -> list[dict[str, str]]:
        raise DataSourceUnavailableError("Home Assistant is not configured. Entity listing is unavailable.")
