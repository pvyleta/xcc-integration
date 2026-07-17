# CLAUDE.md

Guidance for working in this repo. Keep it current when architecture or workflows change.

## What this is

A **Home Assistant custom integration** (`custom_components/xcc/`, domain `xcc`) for AC Heating **XCC heat pump controllers** (with PV). It polls the controller over local HTTP, auto-discovers ~470 fields across ~8 pages, and exposes them as HA entities (sensor / binary_sensor / switch / number / select / button). Bilingual EN/CZ. Distributed via HACS; `quality_scale: silver`, `iot_class: local_polling`.

Plus separate **standalone tooling at repo root** — `xcc_cli.py`, `xcc_scraper.py`, `find_hidden_switches.py` — used for exploring controllers and discovering fields. These do **not** share code with the integration (see Tooling caveats).

## Commands

```bash
# Unit tests (no Home Assistant) — fast, what CI runs first
pip install -r tests/requirements-test.txt
pytest tests/ -v --tb=short

# Full suite WITH Home Assistant + coverage (CI's test-ha job)
pip install -r requirements-dev.txt
pytest tests/ -v --tb=short --cov=custom_components/xcc --cov-report=xml

ruff check . && ruff format --check .          # lint (non-blocking in CI)
python -m compileall -q custom_components/xcc tests   # syntax gate
python find_hidden_switches.py                  # regenerate hidden_switches_report.txt (offline)
```

The same `tests/` dir is run by both CI jobs. HA-dependent tests guard themselves with `pytest.importorskip("homeassistant")` so they collect-skip under the no-HA unit job. Tests that lack a sample file or parser call `pytest.skip(...)` rather than fail.

## Releasing (tag-driven, version-locked)

1. Bump `version` in `custom_components/xcc/manifest.json`.
2. Commit, then push tag `vX.Y.Z` — **must exactly equal** the manifest version (minus the `v`).
3. CI's `verify-manifest` job fails the release if they differ; `publish-release` only runs if `lint`, `syntax`, `test-unit`, `test-ha`, and `verify-manifest` all pass. No green CI → no GitHub Release.

`const.VERSION` is read dynamically from `manifest.json` at import — manifest is the single source of truth.

## Architecture (the integration)

- **Two-tier page model is the core design.** *Descriptor* pages (lowercase, e.g. `fve.xml`) carry type/UI metadata and are fetched **once** at first refresh into `coordinator.entity_configs`. *Data* pages (UPPERCASE, e.g. `FVE4.XML`) carry live `<INPUT P VALUE NAME>` values and are fetched **every poll**. Page lists: `XCC_DESCRIPTOR_PAGES` / `XCC_DATA_PAGES` in [const.py](custom_components/xcc/const.py). Keep the lowercase↔UPPERCASE pairing when adding pages.
- **Coordinator** ([coordinator.py](custom_components/xcc/coordinator.py)) is a `DataUpdateCoordinator`. `_async_update_data`: reuse persistent `XCCClient` → (first run) discover pages + load descriptors → fetch data pages (`asyncio.wait_for(timeout=DEFAULT_TIMEOUT=10s)`) → `parse_xml_entities` per page → `entity_helpers.process_entities` buckets into HA platforms. `coordinator.data` is `{sensors, switches, numbers, selects, buttons, binary_sensors, entities}`.
- **Client** ([xcc_client.py](custom_components/xcc/xcc_client.py)): plain HTTP, **single connection only** (`TCPConnector limit=1`); SHA1-challenge auth (`passhash = sha1(session_id + password)`), session cookie cached to `<config_dir>/.xcc_session_<ip>.json`. Per-IP `asyncio.Lock` serializes re-auth. Inter-request delays (100–200ms) avoid HTTP-500 "max connections".
- **Descriptor parsing** ([descriptor_parser.py](custom_components/xcc/descriptor_parser.py)): XML (and HTML for FVEINV) → entity_config dicts (`prop`, `friendly_name` CZ, `friendly_name_en`, `entity_type`, `unit`, min/max, options, `visData`...).
- **Devices**: one main controller device + fixed sub-devices keyed by page code (FVE, TUV1, OKRUH, SPOT, ...). The sub-device dict in `coordinator._init_device_info` and `_DEVICE_PRIORITY` in [entity_helpers.py](custom_components/xcc/entity_helpers.py) **must stay in sync** — a prop goes to the first priority device that claims it; pages whose device key isn't in `_DEVICE_PRIORITY` are **silently dropped**.
- **Writes**: `coordinator.async_set_entity_value(entity_id, value)` → `value_writer.resolve_property` maps entity_id→prop+internal register NAME → `client.set_value` POSTs `{internal_name: value}` → `async_request_refresh()`. The controller is written by internal register NAME (e.g. `__R44907.0_BOOL_i`), never the human prop.

## Conventions

- **Canonical entity_id is `xcc_<slugified_prop>`.** Every platform forces `self.entity_id` explicitly to avoid HA baking the controller IP into the slug. `format_entity_id_suffix` does the slug but does **not** add the `xcc_` prefix — callers prepend it.
- **unique_id is always `f"{ip_address}_{base_entity_id}"`** (namespaces multiple controllers; `async_regenerate_entity_ids` parses it).
- `_attr_has_entity_name = True` everywhere; `_attr_name` is set to `None` when the feature name equals the device name.
- **Manual metadata fixes go through one table:** `DESCRIPTOR_OVERRIDES` in const.py = `STATUS_XML_DESCRIPTOR` + `HIDDEN_SWITCHES` + `HIDDEN_BINARY_SENSORS`, merged over descriptor output. Don't scatter type fixes elsewhere. To expose a hidden switch: find it in `hidden_switches_report.txt`, add to `HIDDEN_SWITCHES` (see [HIDDEN_SWITCHES.md](HIDDEN_SWITCHES.md)).
- Bilingual: configs carry `friendly_name` (CZ) + `friendly_name_en`; resolution order depends on `coordinator.language` (from `CONF_LANGUAGE`, default English).
- Test imports: rely on `tests/conftest.py` paths; import as `from custom_components.xcc.<mod>` or `from xcc.<mod>`. Never `sys.path.insert` in a test.

## Gotchas

- **Never add `custom_components/xcc/` to `sys.path`** — its `select.py` shadows the stdlib `select` module and breaks the whole test session. `conftest.py` deliberately keeps it off the path.
- **Two base-class lineages, duplicated wiring.** `sensor`/`binary_sensor`/`button` extend `XCCEntity`; `switch`/`number`/`select` extend `CoordinatorEntity` directly and reimplement unique_id/entity_id/device_info/name inline. Changes to entity-id or device logic must be applied in **both** places.
- **Options-flow scan interval is a no-op.** The coordinator reads `scan_interval`/`language` only from `entry.data`, not `entry.options`. Changing scan interval via Configure reloads the entry but polling cadence doesn't change. (`DEFAULT_SCAN_INTERVAL=120s`, distinct from `DEFAULT_TIMEOUT=10s` and the client's 30s aiohttp timeout.)
- **`CONF_REGENERATE_ENTITY_IDS` is a destructive one-shot** (defaults False): renames legacy IP-baked entity_ids to `xcc_*` and drops duplicates, resetting recorder history. Auto-cleared after the sweep. Left off so remove+re-add preserves entity_ids.
- **Don't remove the datetime/POCASI unit guards** in `descriptor_parser._infer_unit_from_context`: the `CAS`→`h` (time) heuristic also matches `POCASI*` weather props AND the substring `TIME` inside `DATETIME`/`TIMESTAMP` (e.g. `FLASH-HEADER*-DATETIME`), all of which are strings — a numeric unit makes HA raise `ValueError` on every read. The carve-out skips `POCASI*` + `DATETIME`/`DATUM`/`DATE`/`TIMESTAMP`; `date`/`time` XML elements force `unit=None` too. Backstop: `sensor.py` strips the unit for any field whose resolved `data_type` is `datetime`/`date`/`time`/`string` (catches data-only `_DT_` fields like `SCAS`).
- **Platforms must NOT call `coordinator.async_config_entry_first_refresh()`.** `__init__.async_setup_entry` runs it once before forwarding platforms; a second call inside a forwarded `async_setup_entry` re-fetches every page and, if it races the per-page timeout, raises `ConfigEntryNotReady` mid-forward — the entry loads partially and that platform's entities stick at `unavailable`. Read the already-loaded `coordinator.data` directly (see `number.py`). Guarded by `tests/test_first_refresh_and_datetime_unit_fix.py`.
- `_BOOL_i` data fields default to **writable switches**, not read-only binary_sensors — pin read-only status flags via `HIDDEN_BINARY_SENSORS` (e.g. the `BLOKYSPOTREBY-OK` routing fix).
- Page discovery and descriptor loading set their loaded-flags to True **even on failure** — they won't retry within a coordinator lifetime; restart HA to re-discover.
- `STATUS.XML` has no paired descriptor; its labels are hardcoded in `STATUS_XML_DESCRIPTOR`.
- `manifest.json` and `strings.json` still mention MQTT/`entity_type`, but the MQTT path was removed — the config flow forces `ENTITY_TYPE_INTEGRATION`. Stale text; `mqtt_discovery.py` no longer exists.
- Two changelogs: [INTEGRATION_CHANGELOG.md](INTEGRATION_CHANGELOG.md) (the HA integration) vs [CHANGELOG.md](CHANGELOG.md) (the CLI tool). Update the right one.

## Standalone tooling caveats

- `xcc_cli.py`, root `xcc_client.py`, and the integration's client are **three separate implementations** (copy-pasted auth/page lists, not shared modules).
- `xcc_cli.py` depends on `field_database.json` + `scripts/analyze_known_pages.py`, **neither of which exists** in the repo — `refresh-db` and most page subcommands are currently broken.
- `xcc_scraper.py` only works via its inline fallback client (the integration-client import path is API-incompatible).
- `find_hidden_switches.py` is offline; it needs pre-existing files under `fresh_tuv_data/` or `tests/sample_data/`.

## Scraping pages from a live controller

The user's live controller is at **192.168.0.50** (default creds `xcc`/`xcc`); the repo's config samples use the placeholder `192.168.1.100`. Because the standalone scraper/CLI are partly broken, the most dependable way to pull a one-off page is a small direct-fetch script:

1. `GET /LOGIN.XML` → grab the `SoftPLC` session cookie.
2. `passhash = sha1(session_id + password)`; `POST {USER, PASS}` to `/RPC/WEBSES/create.asp` (200 + no `<LOGIN>` = success).
3. `GET /<page>` for each page. Use ONE connection, sequential, with ~200 ms gaps (the controller enforces a 1-connection limit → HTTP 500 otherwise).
4. Save **raw bytes** so each file keeps its own encoding declaration — descriptor pages are lowercase UTF-8 (e.g. `fvesoc.xml`), data pages are UPPERCASE `windows-1250` (e.g. `FVESOC1.XML`). New fixtures go in `tests/sample_data/`.

**Logout:** there is no working logout endpoint — `POST /RPC/WEBSES/destroy.asp` just returns "Server disconnected". Free the controller's single connection slot by closing the HTTP session; the server-side `SoftPLC` session then times out on its own.

When adding a page that is **not referenced from `main.xml`** (auto-discovery won't find it — `FVESOC1.XML` was such a case), register it in: `_check_additional_pages` (coordinator.py), the static `XCC_DESCRIPTOR_PAGES`/`XCC_DATA_PAGES` fallback (const.py), `_normalize_page_to_device` if its device key isn't already in `_DEVICE_PRIORITY` (else its entities are silently dropped), and `set_value`'s page routing if its props are writable.
