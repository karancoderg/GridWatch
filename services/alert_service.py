import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

from models.enums import Severity, SensorType
from data.store import GridWatchStore
from config import THRESHOLDS

logger = logging.getLogger(__name__)

@dataclass
class AlertRow:
    severity: Severity
    sensor_type: SensorType
    value: float
    threshold: str           # e.g. "> 250V Critical Swell"
    timestamp: datetime
    station_name: str

def _get_anomaly_reason(sensor_type: SensorType, value: float) -> str:
    """
    Returns a highly human-readable reason for why exactly this reading triggered an alert.
    If the value itself isn't outside physical hardware limits, it defaults to catching
    the mathematical Z-Score anomaly flag naturally!
    """
    if sensor_type not in THRESHOLDS:
        return "Statistical Anomaly"

    bounds = THRESHOLDS[sensor_type]
    
    if sensor_type == SensorType.VOLTAGE:
        # Check Criticals
        if value < bounds[Severity.RED][1]:   return "< 185V Critical Sag"
        if value > bounds[Severity.RED][2]:   return "> 250V Critical Swell"
        # Check Warnings
        if value < bounds[Severity.YELLOW][1]: return "185V-200V Warning"
        if value > bounds[Severity.YELLOW][2]: return "240V-250V Warning"
        
    else:  # Temperature and Load %
        red = bounds[Severity.RED][0]
        yel_low, yel_high = bounds[Severity.YELLOW]
        unit = "°C" if sensor_type == SensorType.TEMPERATURE else "%"
        
        if value > red:                   return f"> {red}{unit} Critical"
        if yel_low <= value <= yel_high:  return f"{yel_low}-{yel_high}{unit} Warning"

    # If the reading bypassed all static limits above, it MUST have been flagged by the standard deviation math.
    return "Statistical Variance (Z-Score)"

def get_alerts_for_station(station_id: str, store: GridWatchStore, limit: int = 20) -> List[AlertRow]:
    """
    Compiles a clean layout of recent anomalies specifically for an overarching UI or station dashboard.
    Uses an advanced but highly readable SQL JOIN to rapidly pull pre-compiled station data directly from the DB.
    """
    query = """
        SELECT 
            r.severity, r.timestamp, r.value,
            s.type as sensor_type,
            st.name as station_name
        FROM readings r
        JOIN sensors s ON r.sensor_id = s.id
        JOIN stations st ON s.station_id = st.id
        WHERE st.id = ? AND r.is_anomaly = 1
        ORDER BY r.timestamp DESC
        LIMIT ?
    """
    
    alerts = []
    
    try:
        with store.get_connection() as conn:
            rows = conn.execute(query, (station_id, limit)).fetchall()
            
            for row in rows:
                # 1. Map SQLite String Types safely back to Python Enums
                s_type = SensorType(row['sensor_type'])
                
                try:
                    sev = Severity(int(row['severity']))
                except ValueError:
                    sev = Severity.RED  # If severity parsing corrupts during an anomaly fetch, assume RED
                
                # 2. Re-hydrate the clean Dataclass instance
                alerts.append(AlertRow(
                    severity=sev,
                    sensor_type=s_type,
                    value=row['value'],
                    threshold=_get_anomaly_reason(s_type, row['value']),
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    station_name=row['station_name']
                ))
                
    except Exception as e:
        logger.error(f"Failed pulling alerts for {station_id}: {e}")
        
    return alerts