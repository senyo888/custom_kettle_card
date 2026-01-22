"""Constants for the Kettle Protocol integration."""

DOMAIN = "kettle_protocol"

CONF_TEMP_SENSOR = "temp_sensor"
CONF_STATUS_SENSOR = "status_sensor"
CONF_START_SWITCH = "start_switch"
CONF_KEEP_WARM_SWITCH = "keep_warm_switch"

CONF_MAX_MINUTES = "max_minutes"
CONF_ABORT_STATUSES = "abort_statuses"
CONF_WARM_VALUE = "warm_value"

DEFAULT_MAX_MINUTES = 30
DEFAULT_ABORT_STATUSES = ["standby"]
DEFAULT_WARM_VALUE = "Warm"

STORE_KEY = f"{DOMAIN}_state"
STORE_VERSION = 1