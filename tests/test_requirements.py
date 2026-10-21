"""Tests for dependency versions."""

import json
from pathlib import Path

import homeassistant.components
import pymodbus

import custom_components.komfovent

HA_MODBUS_DIR = Path(homeassistant.components.__file__).parent / "modbus"
KOMFOVENT_DIR = Path(custom_components.komfovent.__file__).parent


def _pymodbus_requirement(integration_dir: Path) -> str:
    """Return the pymodbus requirement from an integration's manifest."""
    manifest = json.loads((integration_dir / "manifest.json").read_text())
    return next(r for r in manifest["requirements"] if r.startswith("pymodbus"))


def test_pymodbus_matches_home_assistant_pin():
    """Test that we run against the pymodbus version Home Assistant pins."""
    assert _pymodbus_requirement(HA_MODBUS_DIR) == f"pymodbus=={pymodbus.__version__}"


def test_manifest_pymodbus_floor_matches_tested_version():
    """Test that the manifest requires at least the tested pymodbus version."""
    assert _pymodbus_requirement(KOMFOVENT_DIR) == f"pymodbus>={pymodbus.__version__}"
