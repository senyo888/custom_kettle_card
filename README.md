# Custom Kettle Card (Kettle Protocol)

A Home Assistant integration with optional automation package and Blueprint that enforces a **safe, time-limited keep-warm protocol** (default **30 minutes**) for smart kettles, with **live countdown sensors** designed for clean Lovelace UI cards.

![IMG\_5412](https://github.com/user-attachments/assets/fd0f1929-50a7-4f2e-b6dc-d2817a9d0abc)

---

## What this project does

* Starts a **keep-warm protocol** when keep-warm is switched **ON**
* Enforces a **hard maximum keep-warm duration** (default 30 minutes)
* Exposes **live countdown sensors** (`Warm (mm:ss)`)
* Automatically turns keep-warm **OFF** when:

  * the time limit is reached, or
  * the kettle is lifted / reports an idle status (default: `standby`)
* Designed to pair with a **single, polished button-card UI**
* Prevents unsafe **indefinite keep-warm loops**

---

## How this repository is structured (important)

This project intentionally offers **three layers**, so users can choose how much control they want:

### 1. Integration (required)

Installed via HACS.
Provides:

* config flow
* stable entity naming
* sensors used by the UI

### 2. Automations (two options – choose one)

Implements the actual **keep-warm safety logic**:

* **YAML package** (fully transparent, copy-paste)
* **Blueprint** (one-click import)

### 3. Lovelace UI (optional)

A ready-made `button-card` that displays:

* kettle temperature
* live status with countdown
* boil control
* keep-warm toggle

This separation keeps behaviour **visible, editable, and debuggable** inside Home Assistant.

---

## Requirements

* Home Assistant **2024.1+**
* HACS installed
* A smart kettle that provides:

  * a **keep-warm switch entity**
  * a **status sensor entity** (e.g. `heating`, `Warm`, `standby`)

---

## Installation (HACS – Integration)

1. HACS → **Integrations**
2. Menu (⋮) → **Custom repositories**
3. Add this repository URL
4. Category: **Integration**
5. Install **Kettle Protocol**
6. Restart Home Assistant

---

## Integration setup

After restart:

**Settings → Devices & Services → Add Integration → Kettle Protocol**

Configure:

* **Temperature sensor**
  e.g. `sensor.kettle_current_temperature`
* **Status sensor**
  e.g. `sensor.kettle_status`
* **Start / boil switch**
  e.g. `switch.kettle_start`
* **Keep-warm switch**
  e.g. `switch.kettle_heat_preservation`
* **Max keep-warm minutes** (default: 30)
* **Warm status value** (default: `Warm`)
* **Abort statuses** (comma-separated, default: `standby`)

---

<img width="606" height="751" alt="Screenshot 2026-01-22 at 15 36 12" src="https://github.com/user-attachments/assets/3d70b790-3504-46ec-8adb-c309d59a4270" />

---


## Automation options (required for safety logic)

You must choose **one** of the following.

---

### Option A — YAML package (recommended for power users)

This repo includes a complete automation package.

#### Enable packages (if not already enabled)

In `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

#### Install the package

Copy:

```
packages/kettle_protocol.yaml
```

to:

```
/config/packages/kettle_protocol.yaml
```

Restart Home Assistant.

This enables:

* protocol state tracking
* timer enforcement
* timeout shutdown
* lift / standby abort logic

---

### Option B — Blueprint (one-click automation)

A Blueprint is included for users who prefer UI-driven setup.

**Blueprint location:**

```
.blueprints/automation/custom_kettle_card/kettle_keep_warm_protocol.yaml
```

#### Import the Blueprint

1. Home Assistant → **Settings → Automations & Scenes → Blueprints**
2. **Import Blueprint**
3. Paste the raw GitHub URL to the blueprint file (or upload it)

#### Create required helpers

Create these helpers first (Settings → Devices & Services → Helpers):

* **Toggle helper**
  `input_boolean.kettle_keep_warm_protocol`
* **Timer helper**
  `timer.kettle_keep_warm_max` (default: 00:30:00)

#### Create the automation

1. Open the Blueprint → **Create Automation**
2. Select:

   * Keep-warm switch
   * Status sensor
   * Protocol flag helper
   * Protocol timer
3. Adjust duration and abort status if required

---

## Entities created

### Sensors

* `sensor.kettle_status_live`
  → shows `Warm (mm:ss)` while active
* `sensor.kettle_keep_warm_remaining`
  → remaining time (`mm:ss`)

### Binary sensor

* `binary_sensor.kettle_keep_warm_protocol_active`

### Helpers (internal)

* `input_boolean.kettle_keep_warm_protocol`
* `timer.kettle_keep_warm_max`

---

## Lovelace UI (optional)

A ready-made button-card is included:

```
examples/lovelace_button_card.yaml
```

### To use:

1. Open your dashboard
2. Edit → **Raw configuration editor**
3. Paste the contents of the file

The card provides:

* temperature display
* animated heating state
* live countdown
* boil control
* keep-warm toggle

---

## Safety note

This project exists to **prevent unsafe indefinite keep-warm behaviour**.

It does **not** bypass manufacturer protections.
Always follow the kettle manufacturer’s safety guidance.

---

![IMG\_5413](https://github.com/user-attachments/assets/03df6251-09dc-46a5-8a4c-269fc7c1ba96)

---



