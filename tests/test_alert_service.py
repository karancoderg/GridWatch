import tempfile
import os
import pytest
from datetime import datetime
from uuid import uuid4

from models.sensor import Sensor
from models.reading import TelemetryReading
from models.enums import SensorType, Severity
from data.store import GridWatchStore
from services.alert_service import get_alerts_for_station, _get_anomaly_reason

@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp()
    store = GridWatchStore(path)
    
    store.save_station("stat_1", "Test Station", "Labs")
    store.save_sensor(Sensor(id="sens_1", station_id="stat_1", type=SensorType.VOLTAGE, unit="V"))
    store.save_sensor(Sensor(id="sens_2", station_id="stat_1", type=SensorType.TEMPERATURE, unit="C"))
    
    yield store
    
    os.close(fd)
    os.remove(path)


class TestAlertAnomalyReasons:

    def test_voltage_anomaly_descriptions(self):
        # Critical checks
        assert _get_anomaly_reason(SensorType.VOLTAGE, 180.0) == "< 185V Critical Sag"
        assert _get_anomaly_reason(SensorType.VOLTAGE, 260.0) == "> 250V Critical Swell"
        
        # Warning checks
        assert _get_anomaly_reason(SensorType.VOLTAGE, 195.0) == "185V-200V Warning"
        assert _get_anomaly_reason(SensorType.VOLTAGE, 245.0) == "240V-250V Warning"

    def test_temperature_anomaly_descriptions(self):
        assert _get_anomaly_reason(SensorType.TEMPERATURE, 90.0) == "> 80°C Critical"
        assert _get_anomaly_reason(SensorType.TEMPERATURE, 70.0) == "65-80°C Warning"

    def test_statistical_variance_fallback(self):
        # 220V is perfectly nominal!
        # If an anomaly is thrown here, it MUST be a math variance flag
        assert _get_anomaly_reason(SensorType.VOLTAGE, 220.0) == "Statistical Variance (Z-Score)"


class TestGetAlertsIntegration:

    def test_get_alerts_for_station_filters_correctly(self, test_db):
        store = test_db
        
        # 1 normal baseline reading
        store.save_reading(TelemetryReading(
            id=str(uuid4()), sensor_id="sens_1", value=220.0, timestamp=datetime.now(), 
            severity=Severity.GREEN, is_anomaly=False
        ))
        
        # 2 distinct anomalous readings across 2 sensors
        store.save_reading(TelemetryReading(
            id=str(uuid4()), sensor_id="sens_1", value=260.0, timestamp=datetime.now(), 
            severity=Severity.RED, is_anomaly=True
        ))
        store.save_reading(TelemetryReading(
            id=str(uuid4()), sensor_id="sens_2", value=90.0, timestamp=datetime.now(), 
            severity=Severity.RED, is_anomaly=True
        ))
        
        # Retrieve alerts
        alerts = get_alerts_for_station("stat_1", store)
        
        # It should ONLY fetch the 2 anomalies, completely ignoring the GREEN nominal record!
        assert len(alerts) == 2
        
        # Verify SQL JOIN correctly extracted foreign relations mapping back to the Dataclass
        assert alerts[0].station_name == "Test Station"
        assert alerts[0].severity == Severity.RED
        assert "Critical" in alerts[0].threshold
        assert alerts[0].sensor_type in [SensorType.VOLTAGE, SensorType.TEMPERATURE]
