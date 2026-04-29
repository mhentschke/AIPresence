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
