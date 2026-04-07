import os
import tempfile
import sqlite3
import pytest
from datetime import datetime
from uuid import uuid4

from data.store import GridWatchStore
from models.sensor import Sensor
from models.reading import TelemetryReading
from models.enums import SensorType, Severity

@pytest.fixture
def temp_db_path():
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup after tests
    if os.path.exists(path):
        os.remove(path)
        # SQLite WAL mode creates -wal and -shm files, clean them up too
        if os.path.exists(path + "-wal"):
            os.remove(path + "-wal")
        if os.path.exists(path + "-shm"):
            os.remove(path + "-shm")

def test_store_initialization(temp_db_path):
    store = GridWatchStore(temp_db_path)
    
    with store.get_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row['name'] for row in cursor.fetchall()]
        
        assert 'stations' in tables
        assert 'sensors' in tables
        assert 'readings' in tables

def test_save_station_and_sensor(temp_db_path):
    store = GridWatchStore(temp_db_path)
    
    store.save_station("station_1", "Main Substation", "Seattle")
    
    sensor = Sensor(id="sensor_1", station_id="station_1", type=SensorType.VOLTAGE, unit="V")
    store.save_sensor(sensor)
    
    with store.get_connection() as conn:
        s_row = conn.execute("SELECT * FROM stations WHERE id = 'station_1'").fetchone()
        assert s_row is not None
        assert s_row['name'] == "Main Substation"
        
        sen_row = conn.execute("SELECT * FROM sensors WHERE id = 'sensor_1'").fetchone()
        assert sen_row is not None
        sensor_type_val = SensorType.VOLTAGE.value if hasattr(SensorType.VOLTAGE, 'value') else str(SensorType.VOLTAGE)
        assert sen_row['type'] == sensor_type_val

def test_save_and_retrieve_reading(temp_db_path):
    store = GridWatchStore(temp_db_path)
    
    store.save_station("station_1", "Main Substation", "Seattle")
    sensor = Sensor(id="sensor_1", station_id="station_1", type=SensorType.VOLTAGE, unit="V")
    store.save_sensor(sensor)
    
    reading_id = str(uuid4())
    now = datetime.now()
    reading = TelemetryReading(
        id=reading_id,
        sensor_id="sensor_1",
        value=220.5,
        timestamp=now,
        severity=Severity.YELLOW,
        is_anomaly=True
    )
    
    store.save_reading(reading)
    
    recent = store.get_recent_readings("sensor_1", limit=10)
    assert len(recent) == 1
    assert recent[0]['id'] == reading_id
    assert recent[0]['value'] == 220.5
    severity_val = str(getattr(Severity.YELLOW, 'value', Severity.YELLOW))
    assert recent[0]['severity'] == severity_val
    assert int(recent[0]['is_anomaly']) == 1

def test_save_batch_readings(temp_db_path):
    store = GridWatchStore(temp_db_path)
    
    store.save_station("station_1", "North Substation", "Portland")
    sensor = Sensor(id="sens_tmp", station_id="station_1", type=SensorType.TEMPERATURE, unit="C")
    store.save_sensor(sensor)
    
    readings = []
    for i in range(5):
        readings.append(TelemetryReading(
            id=str(uuid4()),
            sensor_id="sens_tmp",
            value=60.0 + i,
            timestamp=datetime.now(),
            severity=Severity.GREEN,
            is_anomaly=False
        ))
        
    store.save_readings_batch(readings)
    
    recent = store.get_recent_readings("sens_tmp", limit=10)
    assert len(recent) == 5
