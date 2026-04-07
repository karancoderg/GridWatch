@dataclass
class TelemetryReading:
    id: str
    sensor_id: str
    value: float
    timestamp: datetime
    severity: Severity = Severity.GREEN
    is_anomaly: bool = False