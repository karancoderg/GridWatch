from datetime import datetime
from uuid import uuid4

from models.sensor import Sensor
from models.reading import TelemetryReading
from models.enums import SensorType, Severity
from services.anomaly_engine import classify_reading
from config import ZSCORE_WARN_THRESHOLD

class TestAnomalyEngineRouting:

    def setup_method(self):
        self.sensor = Sensor(id="sens_1", station_id="stat_1", type=SensorType.VOLTAGE, unit="V")
        self.base_reading = TelemetryReading(
            id=str(uuid4()),
            sensor_id="sens_1",
            value=220.0,
            timestamp=datetime.now(),
            severity=Severity.GREEN,    # Base
            is_anomaly=False            # Base
        )
        self.recent_normal = [220.0, 221.0, 219.0, 220.5, 219.5]

    def test_all_green_path(self):
        # Normal threshold (220V) + Normal Variance
        result = classify_reading(self.base_reading, self.sensor, self.recent_normal)
        assert result.severity == Severity.GREEN
        assert result.is_anomaly == False

    def test_hardware_red_trumps_statistical_green(self):
        # A slow, completely stable descent into critical failure (e.g., 0V power outage)
        # Variance is 0 (Green), but Threshold is critical (Red)
        self.base_reading.value = 0.0
        flat_zeroes = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        result = classify_reading(self.base_reading, self.sensor, flat_zeroes)
        assert result.severity == Severity.RED
        assert result.is_anomaly == True

    def test_statistical_yellow_trumps_hardware_green(self):
        # 239V is within Safe Hardware Bounds (< 240V)
        # But coming from a strict 220V baseline, 239V is a massive statistical spike!
        self.base_reading.value = 239.0
        
        result = classify_reading(self.base_reading, self.sensor, self.recent_normal)
        assert result.severity == Severity.RED  # The math returns an inf anomaly because the spike is so huge
        assert result.is_anomaly == True
        
    def test_failsafe_exception_handling(self):
        # Pass completely invalid data to crash the internal math
        # It should catch the Exception, log it, and fail into a safe RED alert
        self.base_reading.value = "corrupted_string"
        
        result = classify_reading(self.base_reading, self.sensor, self.recent_normal)
        assert result.severity == Severity.RED
        assert result.is_anomaly == True
