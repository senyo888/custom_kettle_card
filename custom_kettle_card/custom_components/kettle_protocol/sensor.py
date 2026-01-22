"""Sensors for the Kettle Protocol integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event, async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    STORE_KEY,
    STORE_VERSION,
    CONF_STATUS_SENSOR,
    CONF_KEEP_WARM_SWITCH,
    CONF_MAX_MINUTES,
    CONF_ABORT_STATUSES,
    CONF_WARM_VALUE,
)

UPDATE_ACTIVE_SECONDS = 1
UPDATE_IDLE_SECONDS = 10


@dataclass
class RuntimeState:
    """Runtime state for the keep‑warm protocol."""
    start_ts: str | None = None  # ISO string marking the start of the protocol


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up Kettle Protocol sensors based on a config entry."""
    store = Store(hass, STORE_VERSION, f"{STORE_KEY}_{entry.entry_id}")
    stored = await store.async_load() or {}
    state = RuntimeState(start_ts=stored.get("start_ts"))

    abort_statuses = _parse_abort_statuses(entry.data.get(CONF_ABORT_STATUSES, "standby"))
    max_minutes = int(entry.data.get(CONF_MAX_MINUTES, 30))
    warm_value = str(entry.data.get(CONF_WARM_VALUE, "Warm"))

    status_entity = entry.data[CONF_STATUS_SENSOR]
    keep_warm_switch = entry.data[CONF_KEEP_WARM_SWITCH]

    coordinator = KettleCoordinator(
        hass=hass,
        entry=entry,
        store=store,
        state=state,
        status_entity=status_entity,
        keep_warm_switch=keep_warm_switch,
        max_minutes=max_minutes,
        warm_value=warm_value,
        abort_statuses=abort_statuses,
    )

    async_add_entities(
        [
            KettleStatusLiveSensor(coordinator),
            KettleRemainingSensor(coordinator),
        ],
        update_before_add=True,
    )

    await coordinator.async_start()


def _parse_abort_statuses(raw: str) -> list[str]:
    """Split comma‑separated abort statuses into a list."""
    parts = [p.strip() for p in str(raw).split(",")]
    return [p for p in parts if p]


class KettleCoordinator:
    """Coordinator for managing the keep‑warm protocol timer and state."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        store: Store,
        state: RuntimeState,
        status_entity: str,
        keep_warm_switch: str,
        max_minutes: int,
        warm_value: str,
        abort_statuses: list[str],
    ):
        self.hass = hass
        self.entry = entry
        self.store = store
        self.state = state
        self.status_entity = status_entity
        self.keep_warm_switch = keep_warm_switch
        self.max_minutes = max_minutes
        self.warm_value = warm_value
        self.abort_statuses = abort_statuses

        self._unsub: callback | None = None
        self._tick_unsub: callback | None = None

    @property
    def is_protocol_active(self) -> bool:
        """Return True if the keep‑warm protocol is active."""
        keep_on = self.hass.states.get(self.keep_warm_switch)
        if not keep_on or keep_on.state != "on":
            return False
        return self.state.start_ts is not None

    def _now(self):
        """Return the current UTC time."""
        return dt_util.utcnow()

    def _start_dt(self):
        """Parse the stored ISO timestamp into a datetime."""
        if not self.state.start_ts:
            return None
        try:
            return dt_util.parse_datetime(self.state.start_ts)
        except Exception:
            return None

    def remaining_td(self) -> timedelta | None:
        """Return the remaining time for the keep‑warm cap as a timedelta."""
        if not self.is_protocol_active:
            return None

        start = self._start_dt()
        if not start:
            return None

        elapsed = self._now() - start
        cap = timedelta(minutes=self.max_minutes)
        rem = cap - elapsed
        if rem.total_seconds() < 0:
            return timedelta(seconds=0)
        return rem

    def remaining_mmss(self) -> str | None:
        """Return the remaining time formatted as MM:SS."""
        rem = self.remaining_td()
        if rem is None:
            return None
        total = int(rem.total_seconds())
        m = total // 60
        s = total % 60
        return f"{m:02d}:{s:02d}"

    def status_live(self) -> str:
        """Return a human‑friendly status with optional countdown."""
        st = self.hass.states.get(self.status_entity)
        s = st.state if st else "unknown"

        # Show Warm with countdown when protocol is active
        if s == self.warm_value and self.is_protocol_active:
            mmss = self.remaining_mmss()
            if mmss:
                return f"Warm ({mmss})"
            return "Warm"

        # Normalize common cases
        if s == "heating":
            return "Heating"
        if s == "standby":
            return "Standby"
        if s == self.warm_value:
            return "Warm"

        return str(s)

    async def _persist(self) -> None:
        """Persist the current runtime state to storage."""
        await self.store.async_save({"start_ts": self.state.start_ts})

    async def _clear(self) -> None:
        """Clear the runtime state and persist."""
        self.state.start_ts = None
        await self._persist()

    async def _ensure_tick(self) -> None:
        """Schedule periodic ticks depending on protocol state."""
        # cancel existing
        if self._tick_unsub:
            self._tick_unsub()
            self._tick_unsub = None

        interval = UPDATE_ACTIVE_SECONDS if self.is_protocol_active else UPDATE_IDLE_SECONDS

        async def _tick(_):
            await self.async_tick()
            await self._ensure_tick()

        self._tick_unsub = async_call_later(self.hass, interval, _tick)

    async def async_tick(self) -> None:
        """Periodic check to enforce timeout and abort conditions."""
        # Abort if kettle goes to standby while protocol active
        st = self.hass.states.get(self.status_entity)
        s = st.state if st else None

        if self.is_protocol_active and s in self.abort_statuses:
            await self._force_keep_warm_off(reason=f"Abort: status '{s}'")
            return

        # Timeout enforcement
        if self.is_protocol_active:
            rem = self.remaining_td()
            if rem is not None and rem.total_seconds() <= 0:
                await self._force_keep_warm_off(reason=f"Max time reached ({self.max_minutes} min)")
                return

    async def _force_keep_warm_off(self, reason: str) -> None:
        """Turn off the keep‑warm switch and clear state with a notification."""
        await self.hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": self.keep_warm_switch},
            blocking=False,
        )
        await self._clear()

        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Kettle",
                "message": f"{reason}. Keep Warm turned OFF.",
            },
            blocking=False,
        )

    @callback
    def _handle_state_event(self, event) -> None:
        """Handle state changes for the keep‑warm switch and status sensor."""
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if not new_state:
            return

        # Keep‑warm switch toggled ON => start timer anchor
        if entity_id == self.keep_warm_switch:
            if new_state.state == "on":
                if self.state.start_ts is None:
                    self.state.start_ts = dt_util.utcnow().isoformat()
                    self.hass.async_create_task(self._persist())
            else:
                # OFF => clear
                if self.state.start_ts is not None:
                    self.state.start_ts = None
                    self.hass.async_create_task(self._persist())

        # Status changes handled in tick (abort), but we can tick immediately
        self.hass.async_create_task(self.async_tick())

    async def async_start(self) -> None:
        """Start listening for state changes and schedule ticks."""
        # Subscribe to keep_warm + status changes
        self._unsub = async_track_state_change_event(
            self.hass,
            [self.keep_warm_switch, self.status_entity],
            self._handle_state_event,
        )
        await self._ensure_tick()

    async def async_stop(self) -> None:
        """Stop listening and cancel ticks."""
        if self._unsub:
            self._unsub()
            self._unsub = None
        if self._tick_unsub:
            self._tick_unsub()
            self._tick_unsub = None


class _BaseKettleSensor(Entity):
    """Base class for Kettle Protocol sensors."""
    _attr_should_poll = False

    def __init__(self, coordinator: KettleCoordinator) -> None:
        self.coordinator = coordinator

    async def async_update(self) -> None:
        # Coordinator ticks itself; entity pulls values on‑demand.
        return


class KettleStatusLiveSensor(_BaseKettleSensor):
    """Sensor representing the live kettle status with optional countdown."""
    _attr_name = "Kettle Status (Live)"
    _attr_unique_id = "kettle_status_live"

    @property
    def state(self) -> str | None:
        return self.coordinator.status_live()

    @property
    def extra_state_attributes(self) -> dict[str, str | bool | int]:  # type: ignore[override]
        return {
            "protocol_active": self.coordinator.is_protocol_active,
            "max_minutes": self.coordinator.max_minutes,
            "remaining": self.coordinator.remaining_mmss() or "—",
        }


class KettleRemainingSensor(_BaseKettleSensor):
    """Sensor representing remaining time in the keep‑warm protocol."""
    _attr_name = "Kettle Keep-Warm Remaining"
    _attr_unique_id = "kettle_keep_warm_remaining"

    @property
    def state(self) -> str:
        return self.coordinator.remaining_mmss() or "—"

    @property
    def icon(self) -> str:
        return "mdi:timer-sand" if self.coordinator.is_protocol_active else "mdi:timer-outline"