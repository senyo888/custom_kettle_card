"""Binary sensor for the Kettle Protocol integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORE_KEY, STORE_VERSION, CONF_KEEP_WARM_SWITCH


class KettleProtocolActiveBinarySensor(Entity):
    """Binary sensor indicating whether the keep‑warm protocol is active."""
    _attr_name = "Kettle Keep-Warm Protocol Active"
    _attr_unique_id = "kettle_keep_warm_protocol_active"
    _attr_device_class = "running"
    _attr_should_poll = True  # very light polling

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, store: Store, keep_warm_switch: str
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.store = store
        self.keep_warm_switch = keep_warm_switch
        self._start_ts: str | None = None

    async def async_update(self) -> None:
        stored = await self.store.async_load() or {}
        self._start_ts = stored.get("start_ts")

    @property
    def is_on(self) -> bool:
        sw = self.hass.states.get(self.keep_warm_switch)
        keep_on = bool(sw and sw.state == "on")
        return keep_on and self._start_ts is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:  # type: ignore[override]
        return {"start_ts": self._start_ts}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Kettle Protocol binary sensor for a config entry."""
    store = Store(hass, STORE_VERSION, f"{STORE_KEY}_{entry.entry_id}")
    keep_warm_switch = entry.data[CONF_KEEP_WARM_SWITCH]
    async_add_entities([
        KettleProtocolActiveBinarySensor(hass, entry, store, keep_warm_switch)
    ])