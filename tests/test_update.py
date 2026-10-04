"""Tests for Komfovent update platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.update import UpdateDeviceClass, UpdateEntityFeature
from homeassistant.exceptions import HomeAssistantError

from custom_components.komfovent import registers
from custom_components.komfovent.const import Controller
from custom_components.komfovent.firmware import FirmwareInfo
from custom_components.komfovent.firmware.uploader import (
    DEVICE_RESTART_DELAY,
    FirmwareUploadError,
)
from custom_components.komfovent.update import KomfoventUpdateEntity

FIRMWARE_FILENAME = "C6_1_5_46_72_P1_1_1_5_48.mbin"


def pack_version(device_type: int, v1: int, v2: int, v3: int, v4: int) -> int:
    """Pack a version into the firmware register format."""
    return device_type << 28 | v1 << 24 | v2 << 20 | v3 << 12 | v4


@pytest.fixture
def firmware_path(tmp_path):
    """Create a firmware file on disk."""
    path = tmp_path / FIRMWARE_FILENAME
    path.write_bytes(b"firmware")
    return path


@pytest.fixture
def mock_store(firmware_path):
    """Create a mock firmware store holding one C6 firmware."""
    store = MagicMock()
    store.get_firmware_info.return_value = FirmwareInfo(
        controller_type="C6",
        filename=FIRMWARE_FILENAME,
        controller_version=(0, 1, 5, 46, 72),
        panel_version=(1, 1, 1, 5, 48),
        file_path=str(firmware_path),
        last_checked_at="2026-01-01T00:00:00+00:00",
    )
    store.get_firmware_path.return_value = firmware_path
    return store


@pytest.fixture
def entity(hass, mock_coordinator, mock_store) -> KomfoventUpdateEntity:
    """Create an update entity with state writes mocked."""
    mock_coordinator.set_cooldown = MagicMock()
    update_entity = KomfoventUpdateEntity(mock_coordinator, mock_store)
    update_entity.hass = hass
    update_entity.async_write_ha_state = MagicMock()
    return update_entity


@pytest.fixture
def mock_uploader():
    """Patch the firmware uploader and the restart wait."""
    with (
        patch(
            "custom_components.komfovent.update.FirmwareUploader", autospec=True
        ) as uploader_class,
        patch(
            "custom_components.komfovent.update.asyncio.sleep", AsyncMock()
        ) as mock_sleep,
    ):
        uploader_class.get_restart_delay.return_value = DEVICE_RESTART_DELAY
        uploader_class.return_value.async_upload_firmware = AsyncMock(return_value=True)
        uploader_class.sleep = mock_sleep
        yield uploader_class


def test_attributes(entity):
    """Test static entity attributes."""
    assert entity.unique_id == "test_entry_id_firmware_update"
    assert entity.device_class == UpdateDeviceClass.FIRMWARE
    assert entity.supported_features == (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )
    assert entity.release_url is None
    assert entity.entity_picture is None
    assert entity.in_progress is False


def test_installed_version(entity, mock_coordinator):
    """Test installed version is the functional version."""
    assert entity.installed_version == "38"


@pytest.mark.parametrize("data", [None, {}, {registers.REG_FIRMWARE: 0}])
def test_installed_version_unknown(entity, mock_coordinator, data):
    """Test installed version is unknown without firmware register data."""
    mock_coordinator.data = data

    assert entity.installed_version is None
    assert entity._is_firmware_supported is False


def test_invalid_firmware_register(entity, mock_coordinator):
    """Test a non-numeric firmware register is handled."""
    mock_coordinator.data = {registers.REG_FIRMWARE: "invalid"}

    assert entity.installed_version is None
    assert entity._is_firmware_supported is False


def test_latest_version(entity, mock_store):
    """Test latest version and summary come from the store."""
    assert entity.latest_version == "72"
    assert entity.release_summary == FIRMWARE_FILENAME
    mock_store.get_firmware_info.assert_called_with("C6")


def test_latest_version_without_firmware(entity, mock_store):
    """Test latest version is unknown when no firmware was downloaded."""
    mock_store.get_firmware_info.return_value = None

    assert entity.latest_version is None
    assert entity.release_summary is None


def test_latest_version_unknown_controller(entity, mock_coordinator):
    """Test latest version is unknown for unsupported controllers."""
    mock_coordinator.controller = Controller.NA

    assert entity.latest_version is None
    assert entity.release_summary is None


@pytest.mark.parametrize(
    ("last_update_success", "data", "expected"),
    [
        (True, {registers.REG_FIRMWARE: 1}, True),
        (False, {registers.REG_FIRMWARE: 1}, False),
        (True, None, False),
    ],
)
def test_available(entity, mock_coordinator, last_update_success, data, expected):
    """Test availability follows the coordinator."""
    mock_coordinator.last_update_success = last_update_success
    mock_coordinator.data = data

    assert entity.available is expected


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ((1, 3, 15, 1), True),
        ((1, 3, 14, 99), False),
        ((1, 5, 46, 72), True),
    ],
)
def test_is_firmware_supported(entity, mock_coordinator, version, expected):
    """Test minimum firmware version for updates."""
    mock_coordinator.data = {registers.REG_FIRMWARE: pack_version(0, *version)}

    assert entity._is_firmware_supported is expected


async def test_install(entity, mock_coordinator, mock_uploader, firmware_path):
    """Test install uploads firmware, waits for restart and refreshes."""
    await entity.async_install(None, backup=False)

    mock_uploader.assert_called_once_with(entity.hass, "192.168.1.100", password="user")
    mock_uploader.return_value.async_upload_firmware.assert_awaited_once_with(
        firmware_path
    )
    mock_coordinator.set_cooldown.assert_called_once_with(DEVICE_RESTART_DELAY)
    mock_uploader.sleep.assert_awaited_once_with(DEVICE_RESTART_DELAY)
    mock_coordinator.async_request_refresh.assert_awaited_once()
    assert entity.in_progress is False
    assert entity.async_write_ha_state.call_count == 2


async def test_install_already_in_progress(entity, mock_uploader):
    """Test a second install is rejected while one is running."""
    entity._installing = True

    with pytest.raises(HomeAssistantError, match="already in progress"):
        await entity.async_install(None, backup=False)

    mock_uploader.assert_not_called()


async def test_install_unsupported_firmware(entity, mock_coordinator, mock_uploader):
    """Test install is rejected for too old firmware."""
    mock_coordinator.data = {registers.REG_FIRMWARE: pack_version(0, 1, 3, 14, 1)}

    with pytest.raises(HomeAssistantError, match="not supported"):
        await entity.async_install(None, backup=False)

    mock_uploader.assert_not_called()


async def test_install_unknown_controller(entity, mock_coordinator, mock_uploader):
    """Test install is rejected for unsupported controllers."""
    mock_coordinator.controller = Controller.NA

    with pytest.raises(HomeAssistantError, match="Unknown controller type"):
        await entity.async_install(None, backup=False)

    mock_uploader.assert_not_called()


@pytest.mark.parametrize("missing", ["path", "file"])
async def test_install_without_firmware_file(
    entity, mock_store, mock_uploader, firmware_path, missing
):
    """Test install is rejected when the firmware file is unavailable."""
    if missing == "path":
        mock_store.get_firmware_path.return_value = None
    else:
        firmware_path.unlink()

    with pytest.raises(HomeAssistantError, match="not available"):
        await entity.async_install(None, backup=False)

    mock_uploader.assert_not_called()


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (FirmwareUploadError("Login failed"), "Firmware upload failed: Login failed"),
        (RuntimeError("boom"), "Firmware update failed: boom"),
    ],
)
async def test_install_failure(entity, mock_coordinator, mock_uploader, error, message):
    """Test upload failures are raised and progress is reset."""
    mock_uploader.return_value.async_upload_firmware.side_effect = error

    with pytest.raises(HomeAssistantError, match=message):
        await entity.async_install(None, backup=False)

    mock_coordinator.set_cooldown.assert_not_called()
    assert entity.in_progress is False
