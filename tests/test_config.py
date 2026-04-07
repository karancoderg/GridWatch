from models.enums import SensorType, Severity
from config import THRESHOLDS, ZSCORE_WINDOW, ZSCORE_WARN_THRESHOLD, ZSCORE_CRIT_THRESHOLD, STATUS_LOOKBACK

def test_threshold_keys_exist():
    assert SensorType.VOLTAGE in THRESHOLDS
    assert SensorType.TEMPERATURE in THRESHOLDS
    assert SensorType.LOAD in THRESHOLDS

def test_voltage_thresholds():
    assert THRESHOLDS[SensorType.VOLTAGE][Severity.YELLOW] == (185, 200, 240, 250)
    assert THRESHOLDS[SensorType.VOLTAGE][Severity.RED] == (0, 185, 250, 9999)

def test_temperature_thresholds():
    assert THRESHOLDS[SensorType.TEMPERATURE][Severity.YELLOW] == (65, 80)
    assert THRESHOLDS[SensorType.TEMPERATURE][Severity.RED] == (80, 9999)

def test_load_thresholds():
    assert THRESHOLDS[SensorType.LOAD][Severity.YELLOW] == (75, 90)
    assert THRESHOLDS[SensorType.LOAD][Severity.RED] == (90, 100)

def test_zscore_constants():
    assert ZSCORE_WINDOW == 20
    assert ZSCORE_WARN_THRESHOLD == 3.0
    assert ZSCORE_CRIT_THRESHOLD == 5.0
    assert STATUS_LOOKBACK == 50