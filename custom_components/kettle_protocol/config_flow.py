"""Config flow for the Kettle Protocol integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_TEMP_SENSOR,
    CONF_STATUS_SENSOR,
    CONF_START_SWITCH,
    CONF_KEEP_WARM_SWITCH,
    CONF_MAX_MINUTES,
    CONF_ABORT_STATUSES,
    CONF_WARM_VALUE,
    DEFAULT_MAX_MINUTES,
    DEFAULT_ABORT_STATUSES,
    DEFAULT_WARM_VALUE,
)


class KettleProtocolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kettle Protocol."""
    VERSION = 1

    async def async_step_user(self, user_input=None):  # type: ignore[override]
        """Handle the initial step."""
        if user_input is not None:
            # Normalize abort statuses: user_input gives a string, convert to comma separated string stored
            return self.async_create_entry(title="Kettle Protocol", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(CONF_STATUS_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(CONF_START_SWITCH): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch"])
                ),
                vol.Required(CONF_KEEP_WARM_SWITCH): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch"])
                ),
                vol.Optional(CONF_MAX_MINUTES, default=DEFAULT_MAX_MINUTES): vol.Coerce(int),
                vol.Optional(CONF_WARM_VALUE, default=DEFAULT_WARM_VALUE): str,
                vol.Optional(CONF_ABORT_STATUSES, default=",".join(DEFAULT_ABORT_STATUSES)): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)