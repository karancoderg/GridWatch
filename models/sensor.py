from dataclasses import dataclass
from models.enums import SensorType
@dataclass
class Sensor:
    id: str
    station_id: str
    type: SensorType          # VOLTAGE | TEMPERATURE | LOAD
    unit: str