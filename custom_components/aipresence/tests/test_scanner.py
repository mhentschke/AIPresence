"""Tests for AIPresence BLE scanner (scanner.py) and scanner sensor entity."""

from __future__ import annotations

import struct
import time
from unittest.mock import MagicMock

from custom_components.aipresence.const import DEFAULT_BEACON_TIMEOUT, DOMAIN
from custom_components.aipresence.scanner import (
    ScannerManager,
    extract_beacon_id,
    extract_ibeacon_id,
)
from custom_components.aipresence.sensor import AIPresenceScannerSensor
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

# ---------------------------------------------------------------------------
# Helpers to build mock BLE advertisements
# ---------------------------------------------------------------------------

IBEACON_UUID = "12345678-1234-1234-1234-123456789abc"
IBEACON_MAJOR = 1
IBEACON_MINOR = 2


def _build_ibeacon_manufacturer_data(
    uuid_str: str = IBEACON_UUID,
    major: int = IBEACON_MAJOR,
    minor: int = IBEACON_MINOR,
) -> dict[int, bytes]:
    """Build Apple iBeacon manufacturer data dict keyed by company ID."""
    uuid_hex = uuid_str.replace("-", "")
    uuid_bytes = bytes.fromhex(uuid_hex)
    # type=0x02, length=0x15, uuid (16), major (2), minor (2), tx_power (1)
    payload = bytes([0x02, 0x15]) + uuid_bytes + struct.pack(">HH", major, minor) + bytes([0xC5])
    return {0x004C: payload}


def _make_service_info(
    *,
    source: str = "AA:BB:CC:DD:EE:FF",
    address: str = "11:22:33:44:55:66",
    rssi: int = -65,
    manufacturer_data: dict[int, bytes] | None = None,
) -> BluetoothServiceInfoBleak:
    """Create a mock BluetoothServiceInfoBleak."""
    adv = MagicMock()
    adv.manufacturer_data = manufacturer_data or {}
    return BluetoothServiceInfoBleak(
        source=source,
        address=address,
        rssi=rssi,
        advertisement=adv,
    )


# ---------------------------------------------------------------------------
# iBeacon extraction tests
# ---------------------------------------------------------------------------


def test_extract_ibeacon_id_valid():
    """Valid iBeacon data returns uuid_major_minor string."""
    info = _make_service_info(manufacturer_data=_build_ibeacon_manufacturer_data())
    result = extract_ibeacon_id(info)
    assert result == f"{IBEACON_UUID}_{IBEACON_MAJOR}_{IBEACON_MINOR}"


def test_extract_ibeacon_id_no_manufacturer_data():
    """No manufacturer data returns None."""
    info = _make_service_info(manufacturer_data={})
    assert extract_ibeacon_id(info) is None


def test_extract_ibeacon_id_wrong_company():
    """Non-Apple company ID returns None."""
    info = _make_service_info(manufacturer_data={0x0059: b"\x02\x15" + b"\x00" * 21})
    assert extract_ibeacon_id(info) is None


def test_extract_ibeacon_id_wrong_type():
    """Apple data with wrong type byte returns None."""
    payload = bytes([0x03, 0x15]) + b"\x00" * 21
    info = _make_service_info(manufacturer_data={0x004C: payload})
    assert extract_ibeacon_id(info) is None


def test_extract_ibeacon_id_too_short():
    """Apple data too short for iBeacon returns None."""
    info = _make_service_info(manufacturer_data={0x004C: b"\x02\x15\x00"})
    assert extract_ibeacon_id(info) is None


def test_extract_beacon_id_ibeacon():
    """extract_beacon_id prefers iBeacon format when available."""
    info = _make_service_info(manufacturer_data=_build_ibeacon_manufacturer_data())
    result = extract_beacon_id(info)
    assert result == f"{IBEACON_UUID}_{IBEACON_MAJOR}_{IBEACON_MINOR}"


def test_extract_beacon_id_mac_fallback():
    """extract_beacon_id falls back to MAC address when no iBeacon data."""
    info = _make_service_info(address="AA:BB:CC:DD:EE:FF", manufacturer_data={})
    result = extract_beacon_id(info)
    assert result == "AA:BB:CC:DD:EE:FF"


# ---------------------------------------------------------------------------
# ScannerManager tests
# ---------------------------------------------------------------------------


def _make_manager(beacon_timeout: int = DEFAULT_BEACON_TIMEOUT) -> ScannerManager:
    """Create a ScannerManager with mocked hass and entry."""
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.options = {}
    return ScannerManager(hass, entry, beacon_timeout=beacon_timeout)


def test_handle_advertisement_stores_beacon():
    """Advertisement data is stored in the scanner's beacon dict."""
    manager = _make_manager()
    info = _make_service_info(source="scanner1", address="DE:AD:BE:EF:00:01", rssi=-70)
    manager._async_handle_advertisement(info, None)

    beacons = manager.get_scanner_beacons("scanner1")
    assert "DE:AD:BE:EF:00:01" in beacons
    assert beacons["DE:AD:BE:EF:00:01"] == -70


def test_handle_advertisement_ibeacon_key():
    """iBeacon advertisements are keyed by uuid_major_minor."""
    manager = _make_manager()
    info = _make_service_info(
        source="scanner1",
        address="DE:AD:BE:EF:00:01",
        rssi=-55,
        manufacturer_data=_build_ibeacon_manufacturer_data(),
    )
    manager._async_handle_advertisement(info, None)

    beacons = manager.get_scanner_beacons("scanner1")
    expected_key = f"{IBEACON_UUID}_{IBEACON_MAJOR}_{IBEACON_MINOR}"
    assert expected_key in beacons
    assert beacons[expected_key] == -55


def test_handle_advertisement_new_scanner_callback():
    """New scanner triggers the entity creation callback."""
    manager = _make_manager()
    cb = MagicMock()
    manager.register_scanner_entity_callback(cb)

    info = _make_service_info(source="new_scanner")
    manager._async_handle_advertisement(info, None)

    cb.assert_called_once_with("new_scanner")


def test_handle_advertisement_existing_scanner_no_callback():
    """Existing scanner does not re-trigger the callback."""
    manager = _make_manager()
    cb = MagicMock()
    manager.register_scanner_entity_callback(cb)

    info = _make_service_info(source="scanner1")
    manager._async_handle_advertisement(info, None)
    manager._async_handle_advertisement(info, None)

    cb.assert_called_once()


def test_beacon_count():
    """get_scanner_beacon_count returns the number of visible beacons."""
    manager = _make_manager()
    for i in range(3):
        info = _make_service_info(source="scanner1", address=f"AA:BB:CC:DD:EE:{i:02X}", rssi=-60 - i)
        manager._async_handle_advertisement(info, None)

    assert manager.get_scanner_beacon_count("scanner1") == 3
    assert manager.get_scanner_beacon_count("unknown") == 0


def test_beacon_expiry():
    """Beacons older than timeout are removed by the expiry task."""
    manager = _make_manager(beacon_timeout=10)

    # Manually insert a stale beacon (timestamp far in the past)
    stale_ts = time.time() - 60
    manager.scanners["scanner1"] = {
        "stale_beacon": (-70, stale_ts),
        "fresh_beacon": (-55, time.time() + 9999),
    }

    manager._async_expire_beacons()

    beacons = manager.get_scanner_beacons("scanner1")
    assert "stale_beacon" not in beacons
    assert "fresh_beacon" in beacons


# ---------------------------------------------------------------------------
# Scanner sensor entity tests
# ---------------------------------------------------------------------------


def test_scanner_sensor_native_value():
    """Scanner sensor state is the beacon count."""
    manager = _make_manager()
    info = _make_service_info(source="scanner1", address="AA:BB:CC:DD:EE:01", rssi=-65)
    manager._async_handle_advertisement(info, None)

    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = AIPresenceScannerSensor(entry, manager, "scanner1")

    assert sensor.native_value == 1


def test_scanner_sensor_attributes():
    """Scanner sensor attributes match {beacon_id: rssi} format."""
    manager = _make_manager()
    info = _make_service_info(source="scanner1", address="AA:BB:CC:DD:EE:01", rssi=-65)
    manager._async_handle_advertisement(info, None)

    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = AIPresenceScannerSensor(entry, manager, "scanner1")

    attrs = sensor.extra_state_attributes
    assert attrs == {"AA:BB:CC:DD:EE:01": -65}


def test_scanner_sensor_device_info():
    """Scanner sensor has its own device registry entry."""
    manager = _make_manager()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = AIPresenceScannerSensor(entry, manager, "esp32_office")

    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, "scanner_esp32_office")}
    assert info["manufacturer"] == "AIPresence"
    assert info["model"] == "BLE Scanner"


def test_scanner_sensor_unique_id():
    """Scanner sensor unique_id is derived from scanner address."""
    manager = _make_manager()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = AIPresenceScannerSensor(entry, manager, "AA:BB:CC:DD:EE:FF")

    assert sensor._attr_unique_id == f"{DOMAIN}_proxy_aa_bb_cc_dd_ee_ff"


# ---------------------------------------------------------------------------
# Friendly name resolution tests
# ---------------------------------------------------------------------------


def _make_device_registry_mock(devices: dict[str, str] | None = None):
    """Create a mock device registry.

    ``devices`` maps scanner addresses to friendly names.
    """
    devices = devices or {}

    def _async_get_device(*, connections=None, identifiers=None):
        # Check connections (network MAC)
        if connections:
            for _type, addr in connections:
                if addr in devices:
                    dev = MagicMock()
                    dev.name = devices[addr]
                    return dev
        # Check identifiers (esphome)
        if identifiers:
            for _domain, addr in identifiers:
                if addr in devices:
                    dev = MagicMock()
                    dev.name = devices[addr]
                    return dev
        return None

    reg = MagicMock()
    reg.async_get_device = _async_get_device
    return reg


def test_resolve_friendly_name_via_mac(monkeypatch):
    """Friendly name is resolved when device registry has a MAC match."""
    manager = _make_manager()
    mock_reg = _make_device_registry_mock({"AA:BB:CC:DD:EE:FF": "Office Proxy"})
    monkeypatch.setattr(
        "custom_components.aipresence.scanner.dr.async_get",
        lambda _hass: mock_reg,
    )

    name = manager._resolve_scanner_friendly_name("AA:BB:CC:DD:EE:FF")
    assert name == "Office Proxy"


def test_resolve_friendly_name_via_esphome_identifier(monkeypatch):
    """Friendly name is resolved via ESPHome identifier fallback."""

    # Registry that only matches on identifiers, not connections
    def _async_get_device(*, connections=None, identifiers=None):
        if identifiers:
            for _domain, addr in identifiers:
                if addr == "esp32_kitchen":
                    dev = MagicMock()
                    dev.name = "Kitchen Proxy"
                    return dev
        return None

    reg = MagicMock()
    reg.async_get_device = _async_get_device

    manager = _make_manager()
    monkeypatch.setattr(
        "custom_components.aipresence.scanner.dr.async_get",
        lambda _hass: reg,
    )

    name = manager._resolve_scanner_friendly_name("esp32_kitchen")
    assert name == "Kitchen Proxy"


def test_resolve_friendly_name_returns_none_when_not_found(monkeypatch):
    """Returns None when no device registry match exists."""
    manager = _make_manager()
    mock_reg = _make_device_registry_mock({})
    monkeypatch.setattr(
        "custom_components.aipresence.scanner.dr.async_get",
        lambda _hass: mock_reg,
    )

    name = manager._resolve_scanner_friendly_name("XX:XX:XX:XX:XX:XX")
    assert name is None


def test_handle_advertisement_stores_friendly_name(monkeypatch):
    """New scanner advertisement triggers friendly name resolution and storage."""
    manager = _make_manager()
    mock_reg = _make_device_registry_mock({"scanner_abc": "Living Room Proxy"})
    monkeypatch.setattr(
        "custom_components.aipresence.scanner.dr.async_get",
        lambda _hass: mock_reg,
    )

    info = _make_service_info(source="scanner_abc", address="11:22:33:44:55:66", rssi=-60)
    manager._async_handle_advertisement(info, None)

    assert manager.get_scanner_friendly_name("scanner_abc") == "Living Room Proxy"


def test_handle_advertisement_stores_none_when_no_name(monkeypatch):
    """Friendly name is None when device registry has no match."""
    manager = _make_manager()
    mock_reg = _make_device_registry_mock({})
    monkeypatch.setattr(
        "custom_components.aipresence.scanner.dr.async_get",
        lambda _hass: mock_reg,
    )

    info = _make_service_info(source="unknown_scanner", address="11:22:33:44:55:66", rssi=-60)
    manager._async_handle_advertisement(info, None)

    assert manager.get_scanner_friendly_name("unknown_scanner") is None


# ---------------------------------------------------------------------------
# Scanner sensor friendly name display tests
# ---------------------------------------------------------------------------


def test_scanner_sensor_uses_friendly_name():
    """Scanner sensor uses friendly name in display name and device info."""
    manager = _make_manager()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = AIPresenceScannerSensor(entry, manager, "AA:BB:CC:DD:EE:FF", friendly_name="Office Proxy")

    assert sensor._attr_name == "AIPresence Proxy Office Proxy"
    info = sensor.device_info
    assert info["name"] == "AIPresence Proxy Office Proxy"


def test_scanner_sensor_falls_back_to_address():
    """Scanner sensor falls back to address when no friendly name."""
    manager = _make_manager()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = AIPresenceScannerSensor(entry, manager, "AA:BB:CC:DD:EE:FF", friendly_name=None)

    assert sensor._attr_name == "AIPresence Proxy AA:BB:CC:DD:EE:FF"
    info = sensor.device_info
    assert info["name"] == "AIPresence Proxy AA:BB:CC:DD:EE:FF"


def test_scanner_sensor_unique_id_unchanged_with_friendly_name():
    """unique_id stays MAC-based regardless of friendly name."""
    manager = _make_manager()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    sensor = AIPresenceScannerSensor(entry, manager, "AA:BB:CC:DD:EE:FF", friendly_name="Office Proxy")

    assert sensor._attr_unique_id == f"{DOMAIN}_proxy_aa_bb_cc_dd_ee_ff"


# ---------------------------------------------------------------------------
# Auto-registration with skip_validation tests
# ---------------------------------------------------------------------------


def test_register_scanner_uses_skip_validation():
    """Registration POST URL includes skip_validation=true query parameter."""
    import asyncio
    from unittest.mock import AsyncMock

    manager = _make_manager()
    manager.backend_url = "http://localhost:5000"

    # Build an async context manager mock for aiohttp response
    mock_response = MagicMock()
    mock_response.status = 200

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_response)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=async_cm)
    manager.session = mock_session

    asyncio.new_event_loop().run_until_complete(manager.async_register_scanner("AA:BB:CC:DD:EE:FF"))

    mock_session.post.assert_called_once()
    url = mock_session.post.call_args[0][0]
    assert "skip_validation=true" in url
    assert url.startswith("http://localhost:5000/beacon_monitors/sensor.aipresence_proxy_aa_bb_cc_dd_ee_ff")


def test_retry_registrations_uses_skip_validation():
    """Retry registration also uses skip_validation=true."""
    import asyncio
    from unittest.mock import AsyncMock

    manager = _make_manager()
    manager.backend_url = "http://localhost:5000"
    manager.known_scanners.add("AA:BB:CC:DD:EE:FF")

    mock_response = MagicMock()
    mock_response.status = 200

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_response)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=async_cm)
    manager.session = mock_session

    asyncio.new_event_loop().run_until_complete(manager.async_retry_registrations())

    mock_session.post.assert_called_once()
    url = mock_session.post.call_args[0][0]
    assert "skip_validation=true" in url
