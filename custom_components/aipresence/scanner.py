"""BLE scanner for AIPresence integration.

Hooks into HA's Bluetooth manager to receive raw BLE advertisements from
ESPHome proxies and local adapters, maintaining per-scanner beacon data.
"""

from __future__ import annotations

import logging
import struct
from datetime import timedelta

import aiohttp
from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.dt import utcnow

from .const import CONF_BACKEND_URL, CONF_BEACON_TIMEOUT, DEFAULT_BEACON_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)

APPLE_COMPANY_ID = 0x004C
IBEACON_TYPE = 0x02
IBEACON_DATA_LENGTH = 0x15  # 21 bytes
BEACON_EXPIRY_INTERVAL = 10  # seconds


def extract_ibeacon_id(service_info: BluetoothServiceInfoBleak) -> str | None:
    """Extract iBeacon UUID/major/minor from manufacturer-specific data.

    Returns a string like ``uuid_major_minor`` or *None* if the advertisement
    does not contain valid iBeacon data.
    """
    advertisement = service_info.advertisement
    manufacturer_data = getattr(advertisement, "manufacturer_data", None)
    if not manufacturer_data:
        return None

    apple_data = manufacturer_data.get(APPLE_COMPANY_ID)
    if apple_data is None or len(apple_data) < 23:
        return None

    # iBeacon: type 0x02, length 0x15 (21 bytes)
    if apple_data[0] != IBEACON_TYPE or apple_data[1] != IBEACON_DATA_LENGTH:
        return None

    uuid_bytes = apple_data[2:18]
    uuid_hex = uuid_bytes.hex()
    uuid_str = f"{uuid_hex[:8]}-{uuid_hex[8:12]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:32]}"
    major = struct.unpack(">H", apple_data[18:20])[0]
    minor = struct.unpack(">H", apple_data[20:22])[0]

    return f"{uuid_str}_{major}_{minor}"


def extract_beacon_id(service_info: BluetoothServiceInfoBleak) -> str:
    """Return a beacon identifier from a BLE advertisement.

    Tries iBeacon extraction first; falls back to the BLE MAC address.
    """
    ibeacon_id = extract_ibeacon_id(service_info)
    if ibeacon_id is not None:
        return ibeacon_id
    return service_info.address


class ScannerManager:
    """Manages per-scanner beacon data from BLE advertisements."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        beacon_timeout: int | None = None,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.beacon_timeout: int = beacon_timeout or entry.options.get(CONF_BEACON_TIMEOUT, DEFAULT_BEACON_TIMEOUT)
        self.backend_url: str = entry.data.get(CONF_BACKEND_URL, "")
        self.session = async_get_clientsession(hass)

        # {scanner_address: {beacon_id: (rssi, timestamp)}}
        self.scanners: dict[str, dict[str, tuple[int, float]]] = {}

        # Set of scanner addresses that have been seen (for entity creation)
        self.known_scanners: set[str] = set()

        # Scanner entity IDs that have been successfully registered with the backend
        self._registered_scanners: set[str] = set()

        # Mapping from scanner_address to the entity_id used for backend registration
        self._scanner_entity_ids: dict[str, str] = {}

        # Mapping from scanner_address to resolved friendly name (or None)
        self._scanner_names: dict[str, str | None] = {}

        # Callbacks for scanner entity management
        self._scanner_entity_callbacks: list = []

        self._unregister_ble: callable | None = None
        self._unregister_expiry: callable | None = None

    # ------------------------------------------------------------------
    # Setup / teardown
    # ------------------------------------------------------------------

    async def async_setup(self) -> None:
        """Register BLE callback and start beacon expiry task."""
        self._unregister_ble = async_register_callback(
            self.hass,
            self._async_handle_advertisement,
            BluetoothCallbackMatcher(),
            BluetoothScanningMode.PASSIVE,
        )

        self._unregister_expiry = async_track_time_interval(
            self.hass,
            self._async_expire_beacons,
            timedelta(seconds=BEACON_EXPIRY_INTERVAL),
        )

    async def async_unload(self) -> None:
        """Unregister BLE callback and stop expiry task."""
        if self._unregister_ble is not None:
            self._unregister_ble()
            self._unregister_ble = None
        if self._unregister_expiry is not None:
            self._unregister_expiry()
            self._unregister_expiry = None

    # ------------------------------------------------------------------
    # BLE advertisement handling
    # ------------------------------------------------------------------

    def _resolve_scanner_friendly_name(self, scanner_address: str) -> str | None:
        """Look up a friendly device name for a scanner address.

        Checks the HA device registry for a device matching the scanner's
        source address (via network MAC connection or ESPHome identifier).
        Returns the device name if found, otherwise ``None``.
        """
        try:
            dev_reg = dr.async_get(self.hass)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Device registry not available for scanner name lookup")
            return None

        # Try matching by network MAC connection
        device = dev_reg.async_get_device(
            connections={(dr.CONNECTION_NETWORK_MAC, scanner_address)},
        )
        if device is None:
            # Try matching by ESPHome identifier
            device = dev_reg.async_get_device(
                identifiers={("esphome", scanner_address)},
            )
        if device is not None and device.name:
            _LOGGER.debug(
                "Resolved scanner %s to friendly name '%s'",
                scanner_address,
                device.name,
            )
            return device.name
        return None

    @callback
    def _async_handle_advertisement(
        self,
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        """Process a BLE advertisement."""
        scanner_address = service_info.source
        beacon_id = extract_beacon_id(service_info)
        rssi = service_info.rssi
        now = utcnow().timestamp()

        scanner_data = self.scanners.setdefault(scanner_address, {})
        scanner_data[beacon_id] = (rssi, now)

        is_new = scanner_address not in self.known_scanners
        if is_new:
            self.known_scanners.add(scanner_address)
            # Resolve friendly name from HA device registry
            friendly_name = self._resolve_scanner_friendly_name(scanner_address)
            self._scanner_names[scanner_address] = friendly_name
            _LOGGER.debug(
                "New BLE scanner detected: %s (friendly_name=%s)",
                scanner_address,
                friendly_name,
            )
            for cb in self._scanner_entity_callbacks:
                cb(scanner_address)

    # ------------------------------------------------------------------
    # Beacon expiry
    # ------------------------------------------------------------------

    @callback
    def _async_expire_beacons(self, _now=None) -> None:
        """Remove beacons not seen within the configured timeout."""
        cutoff = utcnow().timestamp() - self.beacon_timeout
        for scanner_address, beacons in list(self.scanners.items()):
            expired = [bid for bid, (_, ts) in beacons.items() if ts < cutoff]
            for bid in expired:
                del beacons[bid]

    # ------------------------------------------------------------------
    # Scanner data access
    # ------------------------------------------------------------------

    def get_scanner_beacons(self, scanner_address: str) -> dict[str, int]:
        """Return current beacon data for a scanner as ``{beacon_id: rssi}``."""
        beacons = self.scanners.get(scanner_address, {})
        return {bid: rssi for bid, (rssi, _) in beacons.items()}

    def get_scanner_beacon_count(self, scanner_address: str) -> int:
        """Return the number of currently visible beacons for a scanner."""
        return len(self.scanners.get(scanner_address, {}))

    def register_scanner_entity_callback(self, cb) -> None:
        """Register a callback invoked when a new scanner is detected."""
        self._scanner_entity_callbacks.append(cb)

    def get_scanner_friendly_name(self, scanner_address: str) -> str | None:
        """Return the resolved friendly name for a scanner, or None."""
        return self._scanner_names.get(scanner_address)

    # ------------------------------------------------------------------
    # Backend auto-registration
    # ------------------------------------------------------------------

    def _build_entity_id(self, scanner_address: str) -> str:
        """Derive the HA entity_id for a scanner address."""
        safe_name = scanner_address.replace(":", "_").replace(".", "_").lower()
        return f"sensor.{DOMAIN}_proxy_{safe_name}"

    async def async_register_scanner(self, scanner_address: str) -> None:
        """Register a scanner entity with the AIPresence backend.

        Calls ``POST /beacon_monitors/<entity_id>``. Failures are logged
        as warnings without blocking scanner operation.
        """
        entity_id = self._build_entity_id(scanner_address)
        self._scanner_entity_ids[scanner_address] = entity_id

        if entity_id in self._registered_scanners:
            return

        if not self.backend_url:
            _LOGGER.warning("No backend URL configured; skipping scanner registration for %s", entity_id)
            return

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with self.session.post(
                f"{self.backend_url}/beacon_monitors/{entity_id}?skip_validation=true",
                timeout=timeout,
            ) as resp:
                if resp.status in (200, 201, 409):
                    # 409 = already registered, treat as success
                    self._registered_scanners.add(entity_id)
                    _LOGGER.debug("Registered scanner %s with backend", entity_id)
                else:
                    _LOGGER.warning(
                        "Failed to register scanner %s with backend: HTTP %s",
                        entity_id,
                        resp.status,
                    )
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("Failed to register scanner %s with backend: %s", entity_id, err)

    async def async_deregister_scanner(self, scanner_address: str) -> None:
        """Deregister a scanner entity from the AIPresence backend.

        Calls ``DELETE /beacon_monitors/<entity_id>``. Failures are logged
        as warnings without blocking.
        """
        entity_id = self._scanner_entity_ids.get(scanner_address)
        if entity_id is None:
            entity_id = self._build_entity_id(scanner_address)

        if not self.backend_url:
            _LOGGER.warning("No backend URL configured; skipping scanner deregistration for %s", entity_id)
            return

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with self.session.delete(
                f"{self.backend_url}/beacon_monitors/{entity_id}",
                timeout=timeout,
            ) as resp:
                if resp.status in (200, 404):
                    # 404 = already gone, treat as success
                    self._registered_scanners.discard(entity_id)
                    _LOGGER.debug("Deregistered scanner %s from backend", entity_id)
                else:
                    _LOGGER.warning(
                        "Failed to deregister scanner %s from backend: HTTP %s",
                        entity_id,
                        resp.status,
                    )
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("Failed to deregister scanner %s from backend: %s", entity_id, err)

        self._scanner_entity_ids.pop(scanner_address, None)

    async def async_retry_registrations(self) -> None:
        """Retry registration for any scanners not yet registered.

        Intended to be called on each coordinator poll cycle.
        """
        for scanner_address in list(self.known_scanners):
            entity_id = self._scanner_entity_ids.get(scanner_address)
            if entity_id is None or entity_id not in self._registered_scanners:
                await self.async_register_scanner(scanner_address)


async def async_setup_scanner(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> ScannerManager:
    """Create and set up the ScannerManager."""
    manager = ScannerManager(hass, entry)
    await manager.async_setup()
    hass.data[DOMAIN][entry.entry_id + "_scanner"] = manager
    return manager
