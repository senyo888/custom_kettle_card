# Custom Kettle Card (Kettle Protocol)

A tiny Home Assistant custom integration that enforces a **maximum keep‑warm duration** (default **30 minutes**) for a smart kettle and exposes **live countdown sensors** for UI cards.

## What it does

- Starts a protocol timer when keep‑warm is switched **ON**
- Shows **Warm (mm:ss)** via `sensor.kettle_status_live`
- Turns keep‑warm **OFF automatically** when the cap is reached
- Optionally aborts keep‑warm immediately if the kettle reports a “lifted/idle” status (default: `standby`)
- No YAML automations required

## Requirements

- Home Assistant 2023.10+
- Your kettle must provide:
  - a keep‑warm switch entity
  - a status sensor entity

## Installation (HACS)

1. HACS → Integrations → **Custom repositories**
2. Add this repository URL
3. Category: **Integration**
4. Install
5. Restart Home Assistant

## Setup

Settings → Devices & services → Add Integration → **Kettle Protocol**

Enter:

- Temperature sensor entity (e.g. `sensor.kettle_current_temperature`)
- Status sensor entity (e.g. `sensor.kettle_status`)
- Start switch entity (e.g. `switch.kettle_start`)
- Keep‑warm switch entity (e.g. `switch.kettle_heat_preservation`)
- Max keep‑warm minutes (default 30)
- “Warm” status value (default `Warm`)
- Abort statuses (comma separated, default `standby`)

## Entities created

- `sensor.kettle_status_live`
- `sensor.kettle_keep_warm_remaining`
- `binary_sensor.kettle_keep_warm_protocol_active`

## Lovelace UI

This repository includes a Lovelace button‑card example under `examples/lovelace_button_card.yaml`. Copy its content into your dashboard (Raw configuration editor) to display temperature, live status, and a keep‑warm toggle.

## Safety note

This integration is intended to prevent indefinite keep‑warm behavior. Always follow the manufacturer’s safety guidance.