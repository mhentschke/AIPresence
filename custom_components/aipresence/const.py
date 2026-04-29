"""Constants for the AIPresence integration."""

DOMAIN = "aipresence"

CONF_BACKEND_URL = "backend_url"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_BEACON_TIMEOUT = "beacon_timeout"

DEFAULT_SCAN_INTERVAL = 5  # seconds
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 60

DEFAULT_BEACON_TIMEOUT = 30  # seconds
