"""BLE scanner for AIPresence integration.

Hooks into HA's Bluetooth manager to receive raw BLE advertisements from
ESPHome proxies and local adapters, maintaining per-scanner beacon data.
"""

from __future__ import annotations

import logging
import struct
from datetime import timedelta

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.dt import utcnow

from .const import CONF_BEACON_TIMEOUT, DEFAULT_BEACON_TIMEOUT, DOMAIN

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

        # {scanner_address: {beacon_id: (rssi, timestamp)}}
        self.scanners: dict[str, dict[str, tuple[int, float]]] = {}

        # Set of scanner addresses that have been seen (for entity creation)
        self.known_scanners: set[str] = set()

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
            _LOGGER.debug("New BLE scanner detected: %s", scanner_address)
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


async def async_setup_scanner(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> ScannerManager:
    """Create and set up the ScannerManager."""
    manager = ScannerManager(hass, entry)
    await manager.async_setup()
    hass.data[DOMAIN][entry.entry_id + "_scanner"] = manager
    return manager
