import sqlite3
import logging
from contextlib import contextmanager
from typing import List
from models.sensor import Sensor
from models.reading import TelemetryReading
from models.enums import SensorType, Severity

logger = logging.getLogger(__name__)

class GridWatchStore:
    """
    Advanced SQLite Data Store for GridWatch telemetry data.
    Features:
    - WAL mode for better concurrency
    - Context-manager based connection handling
    - Type-hinted methods for all CRUD operations
    - Batch insert operations for high-throughput sensor data
    """
    
    def __init__(self, db_path: str = "gridwatch.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for yielding a database connection safely."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize the database schema with optimizations."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS stations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS sensors (
                    id TEXT PRIMARY KEY,
                    station_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    FOREIGN KEY(station_id) REFERENCES stations(id)
                );
                
                CREATE TABLE IF NOT EXISTS readings (
                    id TEXT PRIMARY KEY,
                    sensor_id TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    is_anomaly INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(sensor_id) REFERENCES sensors(id)
                );
                
                -- Indexes for fast sequence and anomaly querying
                CREATE INDEX IF NOT EXISTS idx_readings_sensor_timestamp 
                ON readings (sensor_id, timestamp DESC);
                
                CREATE INDEX IF NOT EXISTS idx_readings_anomaly 
                ON readings (is_anomaly) WHERE is_anomaly = 1;
            """)

    def save_station(self, station_id: str, name: str, location: str):
        """Insert or update a station."""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO stations (id, name, location) VALUES (?, ?, ?)",
                (station_id, name, location)
            )

    def save_sensor(self, sensor: Sensor):
        """Insert or update a sensor from model."""
        with self.get_connection() as conn:
            sensor_type = getattr(sensor.type, 'value', str(sensor.type))
            conn.execute(
                "INSERT OR REPLACE INTO sensors (id, station_id, type, unit) VALUES (?, ?, ?, ?)",
                (sensor.id, sensor.station_id, sensor_type, sensor.unit)
            )

    def save_reading(self, reading: TelemetryReading):
        """Save a single telemetry reading."""
        with self.get_connection() as conn:
            severity = getattr(reading.severity, 'value', str(reading.severity))
            conn.execute(
                """INSERT INTO readings 
                   (id, sensor_id, value, timestamp, severity, is_anomaly) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (reading.id, reading.sensor_id, reading.value, 
                 reading.timestamp.isoformat(), severity, int(reading.is_anomaly))
            )

    def save_readings_batch(self, readings: List[TelemetryReading]):
        """Efficiently batch insert multiple readings in a single transaction."""
        if not readings:
            return
            
        data = [
            (
                r.id,
                r.sensor_id,
                r.value,
                r.timestamp.isoformat(),
                getattr(r.severity, 'value', str(r.severity)),
                int(r.is_anomaly)
            ) for r in readings
        ]
        
        with self.get_connection() as conn:
            conn.executemany(
                """INSERT INTO readings 
                   (id, sensor_id, value, timestamp, severity, is_anomaly) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                data
            )
            
    def get_recent_readings(self, sensor_id: str, limit: int = 50) -> List[sqlite3.Row]:
        """Fetch the most recent readings for a specific sensor."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM readings WHERE sensor_id = ? ORDER BY timestamp DESC LIMIT ?",
                (sensor_id, limit)
            )
            return cursor.fetchall()