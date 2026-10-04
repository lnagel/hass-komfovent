"""Tests for Komfovent firmware store, checker and uploader."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.komfovent.const import (
    FIRMWARE_CHECK_INTERVAL,
    FIRMWARE_MIN_SIZE,
    FIRMWARE_URLS,
    Controller,
)
from custom_components.komfovent.firmware import (
    FirmwareInfo,
    format_version,
    get_controller_type_for_firmware,
    is_newer_version,
)
from custom_components.komfovent.firmware.checker import FirmwareChecker
from custom_components.komfovent.firmware.store import FirmwareStore
from custom_components.komfovent.firmware.uploader import (
    DEVICE_RESTART_DELAY,
    FirmwareUploader,
    FirmwareUploadError,
)

C6_FILENAME = "C6_1_5_46_72_P1_1_1_5_48.mbin"
C6_LEGACY_FILENAME = "C6_1_3_28_38_20180428.mbin"
C8_FILENAME = "C8_1_2_3_4.mbin"
FIRMWARE_CONTENT = b"\x00" * FIRMWARE_MIN_SIZE

LOGIN_OK_BODY = '<input type="submit" value="Logout">'
UPLOAD_OK_BODY = '<td id="st">Status: firmware uploaded successfully</td>'


def make_firmware_info(
    controller_type: str = "C6",
    filename: str = C6_FILENAME,
    file_path: str = "",
) -> FirmwareInfo:
    """Create a FirmwareInfo for tests."""
    return FirmwareInfo(
        controller_type=controller_type,
        filename=filename,
        controller_version=(0, 1, 5, 46, 72),
        panel_version=(1, 1, 1, 5, 48),
        file_path=file_path,
        last_checked_at="2026-01-01T00:00:00+00:00",
    )


def make_response(
    status: int = 200,
    headers: dict[str, str] | None = None,
    content: bytes = b"",
    text: str = "",
) -> MagicMock:
    """Create a mock aiohttp response usable as an async context manager."""
    response = MagicMock()
    response.status = status
    response.headers = headers or {}
    response.read = AsyncMock(return_value=content)
    response.text = AsyncMock(return_value=text)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    return response


def firmware_response(filename: str = C6_FILENAME, **kwargs) -> MagicMock:
    """Create a mock firmware download response."""
    kwargs.setdefault("content", FIRMWARE_CONTENT)
    return make_response(
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        **kwargs,
    )


@pytest.fixture
def storage_hass(hass, tmp_path):
    """Hass mock whose config path resolves into a temporary directory."""
    hass.config.path = lambda *parts: str(tmp_path.joinpath(*parts))
    return hass


@pytest.fixture
def mock_ha_store():
    """Patch the Home Assistant Store used by FirmwareStore."""
    with patch(
        "custom_components.komfovent.firmware.store.Store", autospec=True
    ) as store_class:
        store_class.return_value.async_load = AsyncMock(return_value=None)
        store_class.return_value.async_save = AsyncMock()
        yield store_class.return_value


@pytest.fixture
def store(storage_hass, mock_ha_store) -> FirmwareStore:
    """Create a FirmwareStore backed by a temporary directory."""
    return FirmwareStore(storage_hass)


@pytest.fixture
def checker(storage_hass, store) -> FirmwareChecker:
    """Create a FirmwareChecker with a real store."""
    return FirmwareChecker(storage_hass, store)


@pytest.fixture
def mock_session():
    """Patch the aiohttp client session used by the checker."""
    session = MagicMock()
    with patch(
        "custom_components.komfovent.firmware.checker.async_get_clientsession",
        return_value=session,
    ):
        yield session


@pytest.fixture
def upload_session():
    """Patch the aiohttp client session used by the uploader."""
    session = MagicMock()
    with patch(
        "custom_components.komfovent.firmware.uploader.async_get_clientsession",
        return_value=session,
    ):
        yield session


@pytest.fixture
def firmware_file(tmp_path) -> Path:
    """Create a firmware file on disk."""
    path = tmp_path / C6_FILENAME
    path.write_bytes(FIRMWARE_CONTENT)
    return path


# ==================== Helper Function Tests ====================


def test_format_version():
    """Test version tuple is formatted without the type element."""
    assert format_version((0, 1, 5, 46, 72)) == "1.5.46.72"


@pytest.mark.parametrize(
    ("installed", "available", "expected"),
    [
        ((0, 1, 5, 46, 71), (0, 1, 5, 46, 72), True),
        ((0, 1, 5, 46, 72), (0, 1, 5, 46, 72), False),
        ((0, 1, 5, 46, 73), (0, 1, 5, 46, 72), False),
    ],
)
def test_is_newer_version(installed, available, expected):
    """Test comparison uses the functional version."""
    assert is_newer_version(installed, available) is expected


@pytest.mark.parametrize(
    ("controller", "expected"),
    [
        (Controller.C6, "C6"),
        (Controller.C6M, "C6"),
        (Controller.C8, "C8"),
        (Controller.NA, "NA"),
    ],
)
def test_get_controller_type_for_firmware(controller, expected):
    """Test controller to firmware type mapping."""
    assert get_controller_type_for_firmware(controller) == expected


# ==================== FirmwareStore Tests ====================


class TestFirmwareStore:
    """Tests for FirmwareStore."""

    async def test_load_without_stored_data(self, store):
        """Test loading with no stored data starts empty."""
        await store.async_load()

        assert store.get_firmware_info("C6") is None
        assert store.get_latest_version("C6") is None
        assert store.get_firmware_path("C6") is None
        assert await store.async_has_firmware_file("C6") is False

    async def test_load_stored_data(self, store, mock_ha_store):
        """Test loading stored data exposes firmware info."""
        info = make_firmware_info(file_path="/config/.storage/komfovent/fw.mbin")
        mock_ha_store.async_load.return_value = {"firmware": {"C6": info}}

        await store.async_load()

        assert store.get_firmware_info("C6") == info
        assert store.get_latest_version("C6") == "1.5.46.72"
        assert store.get_firmware_path("C6") == Path(info["file_path"])

    async def test_set_and_remove_firmware_info(self, store, mock_ha_store):
        """Test setting and removing firmware info persists changes."""
        info = make_firmware_info()

        await store.async_set_firmware_info("C6", info)
        assert store.get_firmware_info("C6") == info
        mock_ha_store.async_save.assert_awaited_once()

        await store.async_remove_firmware_info("C6")
        assert store.get_firmware_info("C6") is None
        assert mock_ha_store.async_save.await_count == 2

        # Removing a missing entry does not save again
        await store.async_remove_firmware_info("C6")
        assert mock_ha_store.async_save.await_count == 2

    async def test_set_firmware_info_recreates_missing_key(self, store, mock_ha_store):
        """Test firmware info can be set when stored data lacks the key."""
        mock_ha_store.async_load.return_value = {}
        await store.async_load()

        await store.async_set_firmware_info("C8", make_firmware_info("C8"))

        assert store.get_firmware_info("C8") is not None

    async def test_storage_dir(self, store, tmp_path):
        """Test storage directory is created on demand."""
        expected = tmp_path / ".storage" / "komfovent"
        assert store.get_storage_dir() == expected
        assert not expected.exists()

        assert await store.async_ensure_storage_dir() == expected
        assert expected.is_dir()

    async def test_has_firmware_file(self, store, firmware_file):
        """Test firmware file presence is checked on disk."""
        await store.async_set_firmware_info(
            "C6", make_firmware_info(file_path=str(firmware_file))
        )
        assert await store.async_has_firmware_file("C6") is True

        firmware_file.unlink()
        assert await store.async_has_firmware_file("C6") is False

    async def test_cleanup_without_storage_dir(self, store):
        """Test cleanup is a no-op when the storage directory is missing."""
        await store.async_cleanup_old_files({"C6"})

        assert not store.get_storage_dir().exists()

    async def test_cleanup_old_files(self, store):
        """Test cleanup removes only unreferenced firmware files."""
        storage_dir = await store.async_ensure_storage_dir()
        current = storage_dir / C6_FILENAME
        old = storage_dir / C6_LEGACY_FILENAME
        other = storage_dir / "notes.txt"
        for path in (current, old, other):
            path.write_bytes(b"data")
        await store.async_set_firmware_info(
            "C6", make_firmware_info(file_path=str(current))
        )

        await store.async_cleanup_old_files({"C6", "C8"})

        assert current.exists()
        assert not old.exists()
        assert other.exists()

    async def test_cleanup_remove_failure(self, store, caplog):
        """Test cleanup logs and continues when removal fails."""
        storage_dir = await store.async_ensure_storage_dir()
        (storage_dir / C6_LEGACY_FILENAME).write_bytes(b"data")

        with patch(
            "custom_components.komfovent.firmware.store.aio_os.remove",
            AsyncMock(side_effect=OSError("denied")),
        ):
            await store.async_cleanup_old_files(set())

        assert "Failed to remove firmware file" in caplog.text


# ==================== FirmwareChecker Tests ====================


class TestFirmwareChecker:
    """Tests for FirmwareChecker."""

    def test_register_and_unregister(self, checker):
        """Test controller types are tracked by firmware type."""
        checker.register_controller_type(Controller.C6M)
        checker.register_controller_type(Controller.C8)
        checker.register_controller_type(Controller.NA)
        assert checker._active_controller_types == {"C6", "C8"}

        checker.unregister_controller_type(Controller.C6)
        assert checker._active_controller_types == {"C8"}

    async def test_start_and_stop(self, checker):
        """Test start registers the interval once and stop removes it."""
        unsub = MagicMock()
        with (
            patch(
                "custom_components.komfovent.firmware.checker.async_track_time_interval",
                return_value=unsub,
            ) as mock_track,
            patch.object(checker, "async_check_for_updates", AsyncMock()) as mock_check,
        ):
            await checker.async_start()
            await checker.async_start()

            mock_track.assert_called_once()
            assert mock_track.call_args.args[2] == FIRMWARE_CHECK_INTERVAL
            mock_check.assert_awaited_once()

            await mock_track.call_args.args[1](None)
            assert mock_check.await_count == 2

        await checker.async_stop()
        await checker.async_stop()
        unsub.assert_called_once()

    async def test_check_skipped_without_controller_types(self, checker, mock_session):
        """Test no download happens without registered controller types."""
        await checker.async_check_for_updates()

        mock_session.get.assert_not_called()

    async def test_check_skipped_when_in_progress(self, checker, mock_session):
        """Test a concurrent check is skipped."""
        checker.register_controller_type(Controller.C6)
        checker._checking = True

        await checker.async_check_for_updates()

        mock_session.get.assert_not_called()

    async def test_check_downloads_firmware(self, checker, store, mock_session):
        """Test a new firmware is downloaded, stored and old files removed."""
        checker.register_controller_type(Controller.C6)
        storage_dir = await store.async_ensure_storage_dir()
        old = storage_dir / C6_LEGACY_FILENAME
        old.write_bytes(b"old")
        mock_session.get.return_value = firmware_response()

        await checker.async_check_for_updates()

        assert mock_session.get.call_args.args[0] == FIRMWARE_URLS[Controller.C6]
        info = store.get_firmware_info("C6")
        assert info is not None
        assert info["filename"] == C6_FILENAME
        assert info["controller_version"] == (0, 1, 5, 46, 72)
        assert info["panel_version"] == (1, 1, 1, 5, 48)
        assert info["last_checked_at"]
        assert info["file_path"] == str(storage_dir / C6_FILENAME)
        assert (storage_dir / C6_FILENAME).read_bytes() == FIRMWARE_CONTENT
        assert not old.exists()
        assert checker._checking is False

    async def test_check_normalizes_c6m(self, checker, mock_session):
        """Test a C6M type entry is checked as C6."""
        checker._active_controller_types = {"C6M"}
        with patch.object(
            checker, "_async_check_controller_type", AsyncMock()
        ) as mock_check:
            await checker.async_check_for_updates()

        mock_check.assert_awaited_once_with("C6")

    async def test_check_same_filename_is_not_saved_again(
        self, checker, store, mock_session, mock_ha_store
    ):
        """Test an already known firmware is not stored again."""
        checker.register_controller_type(Controller.C6)
        await store.async_set_firmware_info("C6", make_firmware_info())
        mock_ha_store.async_save.reset_mock()
        mock_session.get.return_value = firmware_response()

        await checker.async_check_for_updates()

        mock_ha_store.async_save.assert_not_awaited()

    async def test_check_c8_legacy_filename(self, checker, store, mock_session):
        """Test C8 firmware without panel version is parsed."""
        mock_session.get.return_value = firmware_response(C8_FILENAME)

        await checker.async_force_check("C8")

        assert mock_session.get.call_args.args[0] == FIRMWARE_URLS[Controller.C8]
        info = store.get_firmware_info("C8")
        assert info is not None
        assert info["controller_version"] == (Controller.C8.value, 1, 2, 3, 4)
        assert info["panel_version"] == (0, 0, 0, 0, 0)

    async def test_force_check_all(self, checker):
        """Test force check without a type checks all registered types."""
        with patch.object(
            checker, "async_check_for_updates", AsyncMock()
        ) as mock_check:
            await checker.async_force_check()

        mock_check.assert_awaited_once()

    async def test_check_unknown_controller_type(self, checker, mock_session, caplog):
        """Test an unknown controller type is rejected."""
        await checker.async_force_check("C4")

        mock_session.get.assert_not_called()
        assert "Unknown controller type" in caplog.text

    @pytest.mark.parametrize(
        ("response", "message"),
        [
            (make_response(status=403), "HTTP 403"),
            (make_response(), "Invalid or missing firmware filename"),
            (
                make_response(
                    headers={"Content-Disposition": "attachment; filename=fw.bin"}
                ),
                "Invalid or missing firmware filename",
            ),
            (firmware_response(content=b"small"), "Invalid firmware size"),
            (firmware_response("unknown.mbin"), "Failed to parse firmware filename"),
            (firmware_response(C8_FILENAME), "controller type mismatch"),
        ],
        ids=["http", "no_filename", "extension", "size", "unparsable", "mismatch"],
    )
    async def test_check_rejects_invalid_response(
        self, checker, store, mock_session, caplog, response, message
    ):
        """Test invalid download responses are not stored."""
        mock_session.get.return_value = response

        await checker.async_force_check("C6")

        assert message in caplog.text
        assert store.get_firmware_info("C6") is None

    @pytest.mark.parametrize(
        ("error", "message"),
        [
            (TimeoutError(), "Timeout downloading firmware"),
            (aiohttp.ClientError("boom"), "Error checking firmware"),
        ],
    )
    async def test_check_handles_errors(
        self, checker, store, mock_session, caplog, error, message
    ):
        """Test download errors are logged and not raised."""
        mock_session.get.side_effect = error

        await checker.async_force_check("C6")

        assert message in caplog.text
        assert store.get_firmware_info("C6") is None

    @pytest.mark.parametrize(
        ("header", "expected"),
        [
            ("", None),
            ("attachment", None),
            (f'attachment; filename="{C6_FILENAME}"', C6_FILENAME),
            (f"attachment; filename={C6_FILENAME}", C6_FILENAME),
        ],
    )
    def test_extract_filename(self, checker, header, expected):
        """Test filename extraction from Content-Disposition."""
        assert checker._extract_filename(header) == expected


# ==================== FirmwareUploader Tests ====================


class TestFirmwareUploader:
    """Tests for FirmwareUploader."""

    async def test_upload_success(self, hass, upload_session, firmware_file):
        """Test login followed by upload reports completion."""
        upload_session.post.side_effect = [
            make_response(text=LOGIN_OK_BODY),
            make_response(text=UPLOAD_OK_BODY),
        ]
        progress = MagicMock()
        uploader = FirmwareUploader(hass, "192.168.1.100", password="secret")

        assert await uploader.async_upload_firmware(firmware_file, progress) is True

        login_call, upload_call = upload_session.post.call_args_list
        assert login_call.args[0] == "http://192.168.1.100/g1.html"
        assert login_call.kwargs["data"] == {"1": "user", "2": "secret"}
        assert isinstance(upload_call.kwargs["data"], aiohttp.FormData)
        progress.assert_called_once_with(len(FIRMWARE_CONTENT), len(FIRMWARE_CONTENT))

    async def test_upload_without_status_element(
        self, hass, upload_session, firmware_file, caplog
    ):
        """Test a response without status element is accepted with a warning."""
        upload_session.post.side_effect = [
            make_response(text=LOGIN_OK_BODY),
            make_response(text="<html></html>"),
        ]
        uploader = FirmwareUploader(hass, "192.168.1.100")

        assert await uploader.async_upload_firmware(firmware_file) is True
        assert "No status element found" in caplog.text

    async def test_upload_missing_file(self, hass, upload_session, tmp_path):
        """Test a missing firmware file is rejected."""
        uploader = FirmwareUploader(hass, "192.168.1.100")

        with pytest.raises(FirmwareUploadError, match="not found"):
            await uploader.async_upload_firmware(tmp_path / C6_FILENAME)

        upload_session.post.assert_not_called()

    async def test_upload_invalid_extension(self, hass, upload_session, tmp_path):
        """Test a firmware file with wrong extension is rejected."""
        path = tmp_path / "firmware.bin"
        path.write_bytes(FIRMWARE_CONTENT)
        uploader = FirmwareUploader(hass, "192.168.1.100")

        with pytest.raises(FirmwareUploadError, match="Invalid firmware file"):
            await uploader.async_upload_firmware(path)

    async def test_login_failure(self, hass, upload_session, firmware_file):
        """Test failed login prevents the upload."""
        upload_session.post.return_value = make_response(text="<html>Login</html>")
        uploader = FirmwareUploader(hass, "192.168.1.100")

        with pytest.raises(FirmwareUploadError, match="Login failed"):
            await uploader.async_upload_firmware(firmware_file)

        upload_session.post.assert_called_once()

    @pytest.mark.parametrize(
        ("response", "message"),
        [
            (make_response(status=500), "HTTP 500"),
            (
                make_response(text='<td id="st">Status: Error, wrong file</td>'),
                "Error, wrong file",
            ),
            (
                make_response(text='<td id="st">Status: busy</td>'),
                "Unexpected device response",
            ),
        ],
        ids=["http", "error_status", "unexpected_status"],
    )
    async def test_upload_rejected(
        self, hass, upload_session, firmware_file, response, message
    ):
        """Test device-side upload failures raise an error."""
        upload_session.post.side_effect = [make_response(text=LOGIN_OK_BODY), response]
        uploader = FirmwareUploader(hass, "192.168.1.100")

        with pytest.raises(FirmwareUploadError, match=message):
            await uploader.async_upload_firmware(firmware_file)

    @pytest.mark.parametrize(
        ("errors", "message"),
        [
            ([aiohttp.ClientError("boom")], "Network error"),
            ([TimeoutError()], "Upload timed out"),
            ([make_response(text=LOGIN_OK_BODY), TimeoutError()], "Upload timed out -"),
        ],
        ids=["network", "login_timeout", "upload_timeout"],
    )
    async def test_upload_connection_errors(
        self, hass, upload_session, firmware_file, errors, message
    ):
        """Test connection errors are wrapped in FirmwareUploadError."""
        upload_session.post.side_effect = errors
        uploader = FirmwareUploader(hass, "192.168.1.100")

        with pytest.raises(FirmwareUploadError, match=message):
            await uploader.async_upload_firmware(firmware_file)

    def test_restart_delay(self):
        """Test restart delay is exposed."""
        assert FirmwareUploader.get_restart_delay() == DEVICE_RESTART_DELAY
