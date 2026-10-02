"""Tests for English names missing from controller descriptors."""

import json
from pathlib import Path

from custom_components.xcc.const import ENGLISH_NAME_OVERRIDES, STATUS_XML_DESCRIPTOR


def test_common_data_page_english_name_overrides() -> None:
    """Replace raw Czech register names used by data-only fields."""
    expected = {
        "SCAS": "Controller date and time",
        "SCHYBA": "Controller error code",
        "SNAZEV1": "Controller name",
        "SNAZEV2": "Installation name",
    }

    for prop, english_name in expected.items():
        assert ENGLISH_NAME_OVERRIDES[prop]["friendly_name_en"] == english_name


def test_circulation_pump_status_names() -> None:
    """SOBEH status fields describe pumps, not heating-consumer slots."""
    for index in range(10):
        assert (
            STATUS_XML_DESCRIPTOR[f"SOBEH{index}RUN"]["friendly_name_en"]
            == f"Circulation pump {index} running"
        )
        assert (
            STATUS_XML_DESCRIPTOR[f"SOBEH{index}VIS"]["friendly_name_en"]
            == f"Circulation pump {index} available"
        )


def test_pv_overheating_english_name_overrides() -> None:
    """Avoid mixing a Czech parent-row label with English column labels."""
    expected = {
        "TO-FVEPRETOPENI-PRIORITA": "PV overheating - Priority",
        "TO-FVEPRETOPENI-PREBYTEK": "PV overheating - Minimum surplus",
        "TO-FVEPRETOPENI-T": "PV overheating - Overheat by",
        "TO-FVEPRETOPENI-POVOLENI": "PV overheating - Enable",
    }

    for prop, english_name in expected.items():
        assert ENGLISH_NAME_OVERRIDES[prop]["friendly_name_en"] == english_name


def test_fve_english_name_overrides() -> None:
    """Provide English names for FVE fields whose descriptors are Czech-only."""
    expected = {
        "FVESTATS-SSR-OUTPUT0": "SSR output 1",
        "FVESTATS-SSR-OUTPUT1": "SSR output 2",
        "FVESTATS-SSR-OUTPUT2": "SSR output 3",
        "FVESTATS-SSR-SPOTREBASUM": "Total SSR power",
        "FVE-SSR-OUTPUT0-ENABLED": "SSR output 1 enabled",
        "FVE-NZUCHARGELIMITENABLED": (
            "Charge battery only after the permitted grid export is reached"
        ),
        "FVESTATS-NZUCHARGELIMITACTIVE": "Charging limitation active",
        "FVE-NODISCHRGLOWPRICEENABLED": (
            "Disable battery discharge when the electricity price is low"
        ),
        "FVE-NODISCHRGLOWPRICE": (
            "Do not discharge battery below this electricity price"
        ),
        "FVE-CHARGEATCHEAPHOUR": (
            "Charge battery from the grid when the electricity price is low"
        ),
        "FVE-CHARGEATCHEAPMAXPRICE": (
            "Charge battery from the grid below this electricity price"
        ),
        "FVE-CHARGEATCHEAPMAXSOC": "Stop grid charging above this battery SOC",
        "FVE-CHARGEATCHEAPCHRGPOWER": "Grid charging power",
    }

    for prop, english_name in expected.items():
        assert ENGLISH_NAME_OVERRIDES[prop]["friendly_name_en"] == english_name


def test_backup_slot_english_name_overrides() -> None:
    """Provide distinct English names for all three backup slots."""
    for slot in range(3):
        number = slot + 1
        assert (
            ENGLISH_NAME_OVERRIDES[f"FLASH-HEADER{slot}-NAME"]["friendly_name_en"]
            == f"Backup slot {number} name"
        )
        assert (
            ENGLISH_NAME_OVERRIDES[f"FLASH-HEADER{slot}-VERSION"]["friendly_name_en"]
            == f"Backup slot {number} version"
        )
        assert (
            ENGLISH_NAME_OVERRIDES[f"FLASH-HEADER{slot}-DATETIME"]["friendly_name_en"]
            == f"Backup slot {number} date"
        )


def test_language_field_has_translation_metadata() -> None:
    """Label and describe the language choice in both translation catalogs."""
    integration_dir = Path(__file__).parents[1] / "custom_components" / "xcc"
    catalogs = [
        integration_dir / "strings.json",
        integration_dir / "translations" / "cs.json",
    ]

    for catalog_path in catalogs:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        user_step = catalog["config"]["step"]["user"]
        assert user_step["data"]["language"]
        assert user_step["data_description"]["language"]
