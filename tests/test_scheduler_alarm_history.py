"""Tests for the scheduler and alarm history sensors and their slow-cycle reads."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.util.dt import utcnow
from pymodbus.exceptions import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN, Controller
from custom_components.komfovent.coordinator import (
    SLOW_UPDATE_INTERVAL,
    KomfoventCoordinator,
)
from custom_components.komfovent.sensor import (
    AlarmHistorySensor,
    SchedulerSensor,
    create_sensors,
    decode_alarm_history,
    decode_scheduler_program,
)

from .conftest import load_register_fixture

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

DESC = SensorEntityDescription(key="test", name="Test")

# "Stay at home" program as read from a C6 (Walendów, 2026-09-26): every day,
# away 00:00-08:00, normal 08:00-22:00, away 22:00-24:00.
STAY_AT_HOME_ROW = [127, 1, 0, 480, 2, 480, 1320, 1, 1320, 1440, 0, 0, 0, 0, 0, 0]
# "Working week" program 1, row 0: Mon-Fri, five intervals.
WORKING_WEEK_ROW = [
    31,
    1,
    0,
    360,
    2,
    360,
    480,
    0,
    480,
    960,
    2,
    960,
    1320,
    1,
    1320,
    1440,
]


def _scheduler_data(program: int = 0) -> dict[int, int]:
    """Register data with program 0 and 1 filled, the rest empty."""
    data = dict.fromkeys(
        range(
            registers.REG_SCHEDULER_START,
            registers.REG_SCHEDULER_START + registers.SCHEDULER_SIZE,
        ),
        0,
    )
    program_size = registers.SCHEDULER_ROWS * registers.SCHEDULER_ROW_SIZE
    for i, value in enumerate(STAY_AT_HOME_ROW):
        data[registers.REG_SCHEDULER_START + i] = value
    for i, value in enumerate(WORKING_WEEK_ROW):
        data[registers.REG_SCHEDULER_START + program_size + i] = value
    data[registers.REG_SCHEDULER_MODE] = program
    return data


def _alarm_data(records: list[list[int]]) -> dict[int, int]:
    """Register data for an alarm history with the given records."""
    data = dict.fromkeys(
        range(
            registers.REG_ALARM_HISTORY_COUNT,
            registers.REG_ALARM_HISTORY_START + registers.ALARM_HISTORY_SIZE,
        ),
        0,
    )
    data[registers.REG_ALARM_HISTORY_COUNT] = len(records)
    for n, record in enumerate(records):
        start = (
            registers.REG_ALARM_HISTORY_START + n * registers.ALARM_HISTORY_RECORD_SIZE
        )
        for i, value in enumerate(record):
            data[start + i] = value
    return data


def _at(weekday: int, hour: int, minute: int = 0) -> datetime:
    """Return a local datetime on the given weekday (0 = Monday) of a fixed week."""
    # 2026-09-21 is a Monday; the sensor only looks at weekday, hour and minute
    return datetime(2026, 9, 21 + weekday, hour, minute, tzinfo=UTC)


class TestDecodeScheduler:
    """Tests for decode_scheduler_program."""

    def test_stay_at_home(self):
        """Every-day program decodes to one row with three intervals."""
        rows = decode_scheduler_program(_scheduler_data(), 0)
        assert rows == [
            {
                "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "intervals": [
                    {"mode": "away", "start": "00:00", "end": "08:00"},
                    {"mode": "normal", "start": "08:00", "end": "22:00"},
                    {"mode": "away", "start": "22:00", "end": "24:00"},
                ],
                "_mask": 127,
            }
        ]

    def test_working_week_modes(self):
        """Standby is a valid scheduled mode (mode 0)."""
        rows = decode_scheduler_program(_scheduler_data(), 1)
        assert rows[0]["days"] == ["Mon", "Tue", "Wed", "Thu", "Fri"]
        assert [i["mode"] for i in rows[0]["intervals"]] == [
            "away",
            "normal",
            "standby",
            "normal",
            "away",
        ]

    def test_empty_program(self):
        """A program without rows decodes to an empty list."""
        assert decode_scheduler_program(_scheduler_data(), 3) == []

    def test_unknown_mode_and_invalid_interval(self):
        """An unknown mode number is kept as text, an empty interval is skipped."""
        data = _scheduler_data()
        data[registers.REG_SCHEDULER_START + 1] = 42  # unknown mode
        data[registers.REG_SCHEDULER_START + 4] = 7  # second interval start
        data[registers.REG_SCHEDULER_START + 6] = 7  # ... ends where it starts
        rows = decode_scheduler_program(data, 0)
        assert rows[0]["intervals"][0]["mode"] == "42"
        assert len(rows[0]["intervals"]) == 2

    def test_missing_registers(self):
        """Missing interval registers are skipped, not raised."""
        data = {registers.REG_SCHEDULER_START: 127}
        assert decode_scheduler_program(data, 0) == [
            {
                "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "intervals": [],
                "_mask": 127,
            }
        ]


class TestSchedulerSensor:
    """Tests for SchedulerSensor."""

    @pytest.mark.parametrize(
        ("moment", "expected"),
        [
            (_at(0, 7, 59), "away"),
            (_at(0, 8), "normal"),
            (_at(6, 21, 59), "normal"),
            (_at(6, 22), "away"),
        ],
    )
    def test_current_mode(self, mock_coordinator, moment, expected):
        """State is the mode the active program sets at the current time."""
        mock_coordinator.data = _scheduler_data(0)
        sensor = SchedulerSensor(mock_coordinator, registers.REG_SCHEDULER_MODE, DESC)
        with patch(
            "custom_components.komfovent.sensor.dt_util.now", return_value=moment
        ):
            assert sensor.native_value == expected

    def test_day_not_in_program(self, mock_coordinator):
        """A weekday the active program has no row for gives no state."""
        mock_coordinator.data = _scheduler_data(1)  # Mon-Fri only
        sensor = SchedulerSensor(mock_coordinator, registers.REG_SCHEDULER_MODE, DESC)
        with patch(
            "custom_components.komfovent.sensor.dt_util.now", return_value=_at(5, 12)
        ):
            assert sensor.native_value is None

    def test_time_not_covered(self, mock_coordinator):
        """A time no interval covers gives no state."""
        data = _scheduler_data(0)
        data[registers.REG_SCHEDULER_START + 3] = 60  # first interval now 00:00-01:00
        mock_coordinator.data = data
        sensor = SchedulerSensor(mock_coordinator, registers.REG_SCHEDULER_MODE, DESC)
        with patch(
            "custom_components.komfovent.sensor.dt_util.now", return_value=_at(0, 3)
        ):
            assert sensor.native_value is None

    def test_no_scheduler_data(self, mock_coordinator):
        """Without scheduler registers the state and program are empty."""
        mock_coordinator.data = {registers.REG_SCHEDULER_MODE: 0}
        sensor = SchedulerSensor(mock_coordinator, registers.REG_SCHEDULER_MODE, DESC)
        assert sensor.native_value is None
        assert sensor.extra_state_attributes == {
            "program": "stay_at_home",
            "schedule": [],
            "programs": {},
        }

    def test_no_data(self, mock_coordinator):
        """Without coordinator data the program is unknown."""
        mock_coordinator.data = None
        sensor = SchedulerSensor(mock_coordinator, registers.REG_SCHEDULER_MODE, DESC)
        assert sensor.native_value is None
        assert sensor.extra_state_attributes["program"] is None

    def test_attributes(self, mock_coordinator):
        """Attributes carry the active program and all four programs."""
        mock_coordinator.data = _scheduler_data(1)
        sensor = SchedulerSensor(mock_coordinator, registers.REG_SCHEDULER_MODE, DESC)
        attrs = sensor.extra_state_attributes
        assert attrs["program"] == "working_week"
        assert attrs["schedule"][0]["days"] == ["Mon", "Tue", "Wed", "Thu", "Fri"]
        assert "_mask" not in attrs["schedule"][0]
        assert set(attrs["programs"]) == {
            "stay_at_home",
            "working_week",
            "office",
            "custom",
        }
        assert attrs["programs"]["custom"] == []

    def test_unknown_program_number(self, mock_coordinator):
        """An unknown active program number is reported as text."""
        mock_coordinator.data = _scheduler_data(9)
        sensor = SchedulerSensor(mock_coordinator, registers.REG_SCHEDULER_MODE, DESC)
        assert sensor.extra_state_attributes["program"] == "9"


class TestAlarmHistory:
    """Tests for decode_alarm_history and AlarmHistorySensor."""

    # Two filter warnings as stored on a C6 (Walendów, 2026-09-26).
    RECORDS = [
        [2026, (6 << 8) | 15, (10 << 8) | 50, 0, 0x81],
        [2025, (7 << 8) | 13, (2 << 8) | 8, 15, 0x81],
    ]

    def test_decode(self):
        """Records decode newest first, with code, message and local time."""
        history = decode_alarm_history(_alarm_data(self.RECORDS))
        assert [h["time"] for h in history] == [
            "2026-06-15T10:50:00",
            "2025-07-13T02:08:15",
        ]
        assert {h["code"] for h in history} == {"W1"}
        assert history[0]["message"] != "Unknown"

    def test_count_limits_records(self):
        """Only as many records as the count register says are read."""
        data = _alarm_data(self.RECORDS)
        data[registers.REG_ALARM_HISTORY_COUNT] = 1
        assert len(decode_alarm_history(data)) == 1

    def test_invalid_date_and_unknown_code(self):
        """An impossible date gives no time; an unknown code keeps its number."""
        history = decode_alarm_history(_alarm_data([[2026, (13 << 8) | 1, 0, 0, 0x7E]]))
        assert history == [{"code": "F126", "message": "Unknown", "time": None}]

    def test_missing_registers(self):
        """A count larger than the records read stops at the first missing one."""
        assert decode_alarm_history({registers.REG_ALARM_HISTORY_COUNT: 3}) == []

    def test_sensor_state(self, mock_coordinator):
        """State is the newest alarm code; attributes carry the history."""
        mock_coordinator.data = _alarm_data(self.RECORDS)
        sensor = AlarmHistorySensor(
            mock_coordinator, registers.REG_ALARM_HISTORY_COUNT, DESC
        )
        assert sensor.native_value == "W1"
        assert len(sensor.extra_state_attributes["history"]) == 2

    def test_sensor_empty(self, mock_coordinator):
        """An empty history is an empty string, not unknown."""
        mock_coordinator.data = _alarm_data([])
        sensor = AlarmHistorySensor(
            mock_coordinator, registers.REG_ALARM_HISTORY_COUNT, DESC
        )
        assert sensor.native_value == ""

    def test_sensor_no_data(self, mock_coordinator):
        """Without the history registers the state is unknown."""
        mock_coordinator.data = None
        sensor = AlarmHistorySensor(
            mock_coordinator, registers.REG_ALARM_HISTORY_COUNT, DESC
        )
        assert sensor.native_value is None
        assert sensor.extra_state_attributes == {"history": []}

    @pytest.mark.parametrize(
        "fixture",
        [
            "C6M_registers_NFR61N.json",
            "C6_registers_1.3.17.20.json",
            "C6_registers_01KQJJMJHQ0B3TZMR5140RQ8QM.json",
        ],
    )
    def test_fixtures_count_and_order(self, fixture):
        """On real dumps the count matches the records and times run newest first."""
        data = load_register_fixture(fixture)
        history = decode_alarm_history(data)
        assert len(history) == data[registers.REG_ALARM_HISTORY_COUNT]
        times = [h["time"] for h in history]
        assert None not in times
        assert times == sorted(times, reverse=True)


async def test_scheduler_only_for_c6(mock_coordinator):
    """The scheduler sensor is created for C6/C6M and not for C8."""
    keys = {s.entity_description.key for s in await create_sensors(mock_coordinator)}
    assert {"scheduler", "alarm_history"} <= keys

    mock_coordinator.controller = Controller.C8
    keys = {s.entity_description.key for s in await create_sensors(mock_coordinator)}
    assert "scheduler" not in keys
    assert "alarm_history" in keys


@pytest.fixture
def coordinator_entry():
    """Config entry for a real coordinator with a mocked client."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 502},
        entry_id="slow_entry_id",
    )


def _slow_reads(mock_client: AsyncMock) -> list[int]:
    """Start registers of the scheduler / alarm history reads the client saw."""
    return [
        call.args[0]
        for call in mock_client.read.call_args_list
        if registers.REG_SCHEDULER_START <= call.args[0] < 900
        and call.args[0] != registers.REG_ACTIVE_ALARMS_COUNT
    ]


async def test_slow_blocks_read_once_per_interval(
    hass: HomeAssistant, coordinator_entry
) -> None:
    """Slow blocks are read on the first update, then only after the interval."""
    mock_client = AsyncMock()
    mock_client.read = AsyncMock(return_value={})
    with patch(
        "custom_components.komfovent.coordinator.KomfoventModbusClient",
        return_value=mock_client,
    ):
        coordinator = KomfoventCoordinator(hass, config_entry=coordinator_entry)
        await coordinator._update_slow_blocks()
        first = len(_slow_reads(mock_client))
        assert (
            first == 6
        )  # 256 scheduler registers in 3 reads, 251 alarm registers in 3

        await coordinator._update_slow_blocks()
        assert len(_slow_reads(mock_client)) == first

        coordinator._slow_read_at = (
            utcnow() - SLOW_UPDATE_INTERVAL - timedelta(seconds=1)
        )
        await coordinator._update_slow_blocks()
        assert len(_slow_reads(mock_client)) == 2 * first


async def test_slow_blocks_failure_keeps_previous(
    hass: HomeAssistant, coordinator_entry
) -> None:
    """A failed slow read keeps the previous values and does not raise."""
    mock_client = AsyncMock()
    mock_client.read = AsyncMock(return_value={registers.REG_SCHEDULER_START: 127})
    with patch(
        "custom_components.komfovent.coordinator.KomfoventModbusClient",
        return_value=mock_client,
    ):
        coordinator = KomfoventCoordinator(hass, config_entry=coordinator_entry)
        await coordinator._update_slow_blocks()
        before = dict(coordinator._slow_data)
        read_at = coordinator._slow_read_at

        coordinator._slow_read_at = None
        mock_client.read = AsyncMock(side_effect=ModbusException("boom"))
        await coordinator._update_slow_blocks()
        assert coordinator._slow_data == before
        assert read_at is not None
