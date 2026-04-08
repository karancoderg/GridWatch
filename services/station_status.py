from models.enums import Severity
from data.store import GridWatchStore
from config import STATUS_LOOKBACK

def compute_station_color(station_id: str, store: GridWatchStore) -> Severity:
    """
    Determines the overall health of a station based on its recent sensor telemetry.
    The station's color is defined by the worst active severity across all its sensors.
    """
    worst_severity = Severity.GREEN
    
    with store.get_connection() as conn:
        # Find all sensors attached to this station
        sensors = conn.execute("SELECT id FROM sensors WHERE station_id = ?", (station_id,)).fetchall()
        
        for sensor in sensors:
            readings = store.get_recent_readings(sensor['id'], limit=STATUS_LOOKBACK)
            
            for reading in readings:
                # Convert the saved SQLite string (e.g. "1") back into our Python Enum (Severity.YELLOW)
                try:
                    current_severity = Severity(int(reading['severity']))
                except ValueError:
                    continue # Skip corrupted rows safely
                
                # Upgrade the station alert level if we found a worse reading
                if current_severity.value > worst_severity.value:
                    worst_severity = current_severity
                    
                # Advanced Optimization: If we hit RED, the station is already in critical failure. 
                # There is no need to keep checking the rest of the sensors!
                if worst_severity == Severity.RED:
                    return Severity.RED
                    
    return worst_severity

def get_alert_count(station_id: str, store: GridWatchStore, lookback: int = STATUS_LOOKBACK) -> int:
    """
    Counts how many mathematical anomalies (is_anomaly=True) were flagged at this station recently.
    """
    total_anomalies = 0
    
    # Advanced logic: Asking SQLite to count anomalies directly is much faster 
    # than pulling hundreds of rows into Python and counting them manually with a loop!
    sql_count_anomalies = """
        SELECT COUNT(*) as anomaly_count 
        FROM (
            SELECT is_anomaly 
            FROM readings 
            WHERE sensor_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        )
        WHERE is_anomaly = 1
    """
    
    with store.get_connection() as conn:
        sensors = conn.execute("SELECT id FROM sensors WHERE station_id = ?", (station_id,)).fetchall()
        
        for sensor in sensors:
            result = conn.execute(sql_count_anomalies, (sensor['id'], lookback)).fetchone()
            total_anomalies += result['anomaly_count']
            
    return total_anomalies