from enum import Enum
class Severity(Enum):
    GREEN = 0
    YELLOW = 1
    RED = 2

class SensorType(Enum):
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    LOAD = "load"