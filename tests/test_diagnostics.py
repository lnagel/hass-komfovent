"""Tests for Komfovent diagnostics."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pymodbus import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.diagnostics import (
    ERR_READ_FAILED,
    RANGES,
    _check_response,
    async_get_config_entry_diagnostics,
    dump_registers,
)


class TestCheckResponse:
    """Tests for _check_response helper function."""

    def test_valid_response_passes(self):
        """Test valid response does not raise."""
        mock_response = MagicMock()
        mock_response.isError.return_value = False

        # Should not raise
        _check_response(mock_response)

    def test_error_response_raises(self):
        """Test error response raises ModbusException."""
        mock_response = MagicMock()
        mock_response.isError.return_value = True

        with pytest.raises(ModbusException, match=ERR_READ_FAILED):
            _check_response(mock_response)


class TestDumpRegisters:
    """Tests for dump_registers function."""

    async def test_connection_failure_raises(self):
        """Test connection failure raises ConnectionError."""
        with patch(
            "custom_components.komfovent.diagnostics.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            with pytest.raises(ConnectionError, match="Failed to connect"):
                await dump_registers("192.168.1.100", 502)

    async def test_successful_block_read(self):
        """Test successful block read returns registers."""
        with patch(
            "custom_components.komfovent.diagnostics.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()

            # Mock successful response
            mock_response = MagicMock()
            mock_response.isError.return_value = False
            mock_response.registers = [1, 2, 3]
            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            result = await dump_registers("192.168.1.100", 502)

            assert len(result) > 0
            mock_client.close.assert_called_once()

    async def test_block_read_failure_fallback_to_individual(self):
        """Test block read failure falls back to individual reads."""
        with patch(
            "custom_components.komfovent.diagnostics.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()

            call_count = [0]

            def make_response(*args, **kwargs):
                call_count[0] += 1
                response = MagicMock()
                # First call in each range is block read, make it fail
                # Then individual reads succeed
                if call_count[0] % 2 == 1:
                    response.isError.return_value = True
                else:
                    response.isError.return_value = False
                    response.registers = [42]
                return response

            mock_client.read_holding_registers = AsyncMock(side_effect=make_response)

            mock_client_class.return_value = mock_client

            result = await dump_registers("192.168.1.100", 502)

            # Should have results from individual reads
            assert len(result) > 0
            mock_client.close.assert_called_once()

    async def test_all_reads_fail(self):
        """Test when all reads fail returns empty dict."""
        with patch(
            "custom_components.komfovent.diagnostics.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()

            # All reads fail
            error_response = MagicMock()
            error_response.isError.return_value = True
            mock_client.read_holding_registers = AsyncMock(return_value=error_response)

            mock_client_class.return_value = mock_client

            result = await dump_registers("192.168.1.100", 502)

            assert result == {}
            mock_client.close.assert_called_once()

    async def test_client_closed_on_exception(self):
        """Test client is closed even when exception occurs."""
        with patch(
            "custom_components.komfovent.diagnostics.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.close = MagicMock()
            mock_client.read_holding_registers = AsyncMock(
                side_effect=RuntimeError("Unexpected error")
            )

            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError):
                await dump_registers("192.168.1.100", 502)

            mock_client.close.assert_called_once()


class TestAsyncGetConfigEntryDiagnostics:
    """Tests for async_get_config_entry_diagnostics function."""

    async def test_returns_diagnostics(self, hass):
        """Test returns diagnostics data structure."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
            },
        )

        mock_coordinator = MagicMock()
        mock_coordinator.data = {"test": "data"}
        hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

        with patch(
            "custom_components.komfovent.diagnostics.dump_registers",
            new_callable=AsyncMock,
            return_value={1: [1, 2, 3]},
        ):
            result = await async_get_config_entry_diagnostics(hass, entry)

        assert "config_entry" in result
        assert "registers" in result
        assert "coordinator_data" in result
        assert result["registers"] == {1: [1, 2, 3]}
        assert result["coordinator_data"] == {"test": "data"}

    async def test_handles_connection_error(self, hass):
        """Test handles connection error gracefully."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
            },
        )

        mock_coordinator = MagicMock()
        mock_coordinator.data = {"test": "data"}
        hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

        with patch(
            "custom_components.komfovent.diagnostics.dump_registers",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Failed to connect"),
        ):
            result = await async_get_config_entry_diagnostics(hass, entry)

        assert result["registers"] == {}
        assert result["coordinator_data"] == {"test": "data"}

    async def test_handles_modbus_exception(self, hass):
        """Test handles ModbusException gracefully."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
            },
        )

        mock_coordinator = MagicMock()
        mock_coordinator.data = {}
        hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

        with patch(
            "custom_components.komfovent.diagnostics.dump_registers",
            new_callable=AsyncMock,
            side_effect=ModbusException("Read failed"),
        ):
            result = await async_get_config_entry_diagnostics(hass, entry)

        assert result["registers"] == {}


class TestConstants:
    """Tests for diagnostics constants."""

    def test_ranges_defined(self):
        """Test RANGES constant is properly defined."""
        assert len(RANGES) > 0
        for start, count in RANGES:
            assert isinstance(start, int)
            assert isinstance(count, int)
            assert start > 0
            assert count > 0
