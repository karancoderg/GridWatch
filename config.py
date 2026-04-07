from models.enums import SensorType, Severity

THRESHOLDS = {
    SensorType.VOLTAGE: {
        Severity.YELLOW: (185, 200, 240, 250),  # (low_warn, low_safe, high_safe, high_warn)
        Severity.RED:    (0,   185, 250, 9999),
    },
    SensorType.TEMPERATURE: {
        Severity.YELLOW: (65, 80),
        Severity.RED:    (80, 9999),
    },
    SensorType.LOAD: {
        Severity.YELLOW: (75, 90),
        Severity.RED:    (90, 100),
    },
}

ZSCORE_WINDOW = 20          # rolling window size
ZSCORE_WARN_THRESHOLD = 3.0
ZSCORE_CRIT_THRESHOLD = 5.0
STATUS_LOOKBACK = 50        # readings to check for station color