import tempfile
import os
import pytest
from datetime import datetime
from uuid import uuid4

from models.sensor import Sensor
from models.reading import TelemetryReading
from models.enums import SensorType, Severity
from data.store import GridWatchStore
from services.station_status import compute_station_color, get_alert_count

@pytest.fixture
def test_db():
    """
    Spins up an isolated, temporary SQLite GridWatch database that destructs automatically.
    """
    fd, path = tempfile.mkstemp()
    store = GridWatchStore(path)
    
    # 1. Setup Baseline Station
    store.save_station("stat_1", "Test Station", "Labs")
    
    # 2. Setup Baseline Sensors attached to that Station
    store.save_sensor(Sensor(id="sens_1", station_id="stat_1", type=SensorType.VOLTAGE, unit="V"))
    store.save_sensor(Sensor(id="sens_2", station_id="stat_1", type=SensorType.TEMPERATURE, unit="C"))
    
    yield store
    
    os.close(fd)
    os.remove(path)


class TestStationStatus:

    def test_compute_station_color_escalation(self, test_db):
        store = test_db
        
        # 1. Baseline - No Readings: Should default to Green
        assert compute_station_color("stat_1", store) == Severity.GREEN
        
        # 2. Add Green data -> Remains Green
        store.save_reading(TelemetryReading(
            id=str(uuid4()), sensor_id="sens_1", value=220.0, timestamp=datetime.now(), 
            severity=Severity.GREEN, is_anomaly=False
        ))
        assert compute_station_color("stat_1", store) == Severity.GREEN
        
        # 3. Add Yellow data to second sensor -> Evaluates to Yellow
        store.save_reading(TelemetryReading(
            id=str(uuid4()), sensor_id="sens_2", value=75.0, timestamp=datetime.now(), 
            severity=Severity.YELLOW, is_anomaly=True
        ))
        assert compute_station_color("stat_1", store) == Severity.YELLOW
        
        # 4. Add Red data to first sensor -> Evaluates to absolute Red (Hardware Override limits)
        store.save_reading(TelemetryReading(
            id=str(uuid4()), sensor_id="sens_1", value=100.0, timestamp=datetime.now(), 
            severity=Severity.RED, is_anomaly=True
        ))
        assert compute_station_color("stat_1", store) == Severity.RED

    def test_get_alert_count_sql_mapping(self, test_db):
        store = test_db
        
        # Baseline counts match 0
        assert get_alert_count("stat_1", store) == 0
        
        # Batch insert normal hardware metrics and ONE statistical anomaly flag
        readings = [
            TelemetryReading(id=str(uuid4()), sensor_id="sens_1", value=220.0, timestamp=datetime.now(), severity=Severity.GREEN, is_anomaly=False),
            TelemetryReading(id=str(uuid4()), sensor_id="sens_1", value=220.0, timestamp=datetime.now(), severity=Severity.GREEN, is_anomaly=False),
            # Trigger 1
            TelemetryReading(id=str(uuid4()), sensor_id="sens_2", value=120.0, timestamp=datetime.now(), severity=Severity.RED, is_anomaly=True), 
        ]
        store.save_readings_batch(readings)
        assert get_alert_count("stat_1", store) == 1
        
        # Simulate dual sensors breaking concurrently triggering two more alerts Flags
        readings_2 = [
            # Trigger 2
            TelemetryReading(id=str(uuid4()), sensor_id="sens_1", value=0.0, timestamp=datetime.now(), severity=Severity.RED, is_anomaly=True),
            # Trigger 3
            TelemetryReading(id=str(uuid4()), sensor_id="sens_2", value=75.0, timestamp=datetime.now(), severity=Severity.YELLOW, is_anomaly=True),
        ]
        store.save_readings_batch(readings_2)
        
        # The underlying fast SQL count correctly sums anomalies up mathematically
        assert get_alert_count("stat_1", store) == 3
