import logging
from typing import List
from models.reading import TelemetryReading
from models.sensor import Sensor
from models.enums import Severity
from services.threshold import check_threshold
from services.zscore import compute_zscore, evaluate_zscore_severity

logger = logging.getLogger(__name__)

def classify_reading(
    reading: TelemetryReading,
    sensor: Sensor,
    recent_values: List[float]
) -> TelemetryReading:
    """
    Core business logic engine merging static hardware constraints and 
    rolling statistical variance (Z-Score) into a master telemetry determination.
    """
    try:
        # 1. Static physical hardware limit check
        threshold_sev = check_threshold(sensor.type, reading.value)
        
        # 2. Rolling statistical standard deviation check
        zscore = compute_zscore(reading.value, recent_values)
        zscore_sev, statistical_anomaly = evaluate_zscore_severity(zscore)
        
        # 3. Resolve the master overarching state (Pessimistic evaluation)
        final_severity = max(threshold_sev, zscore_sev, key=lambda s: getattr(s, 'value', 0))
        
        # 4. Commit evaluations back into the Telemetry record
        reading.severity = final_severity
        
        # An object is an Anomaly if mathematics flagged it OR if the hardware is literally critically failing (RED)
        reading.is_anomaly = statistical_anomaly or (final_severity == Severity.RED)
        
        return reading
        
    except Exception as e:
        logger.error(f"Anomaly classification engine failure on Sensor {sensor.id}: {e}")
        # In mission-critical software, monitoring blind-spots default to RED
        reading.severity = Severity.RED
        reading.is_anomaly = True
        return reading