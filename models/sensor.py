@dataclass
class Sensor:
    id: str
    station_id: str
    type: SensorType          # VOLTAGE | TEMPERATURE | LOAD
    unit: str