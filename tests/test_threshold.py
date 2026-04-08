from models.enums import SensorType, Severity
from services.threshold import check_threshold

# --- Voltage Tests ---

def test_voltage_green_safe_zone():
    # Nominal and exact bounds (200 - 240)
    assert check_threshold(SensorType.VOLTAGE, 220.0) == Severity.GREEN
    assert check_threshold(SensorType.VOLTAGE, 200.0) == Severity.GREEN
    assert check_threshold(SensorType.VOLTAGE, 240.0) == Severity.GREEN

def test_voltage_yellow_warning_zones():
    # Lower warning (185 - <200)
    assert check_threshold(SensorType.VOLTAGE, 185.0) == Severity.YELLOW
    assert check_threshold(SensorType.VOLTAGE, 199.9) == Severity.YELLOW
    
    # Upper warning (>240 - 250)
    assert check_threshold(SensorType.VOLTAGE, 240.1) == Severity.YELLOW
    assert check_threshold(SensorType.VOLTAGE, 250.0) == Severity.YELLOW

def test_voltage_red_critical_zones():
    # Under minimal sag
    assert check_threshold(SensorType.VOLTAGE, 184.9) == Severity.RED
    assert check_threshold(SensorType.VOLTAGE, 0.0) == Severity.RED
    
    # Over maximal swell
    assert check_threshold(SensorType.VOLTAGE, 250.1) == Severity.RED
    assert check_threshold(SensorType.VOLTAGE, 300.0) == Severity.RED

# --- Temperature Tests ---

def test_temperature_green_safe_zone():
    assert check_threshold(SensorType.TEMPERATURE, 25.0) == Severity.GREEN
    assert check_threshold(SensorType.TEMPERATURE, 64.9) == Severity.GREEN

def test_temperature_yellow_warning_zone():
    # 65 to 80
    assert check_threshold(SensorType.TEMPERATURE, 65.0) == Severity.YELLOW
    assert check_threshold(SensorType.TEMPERATURE, 75.0) == Severity.YELLOW
    assert check_threshold(SensorType.TEMPERATURE, 80.0) == Severity.YELLOW

def test_temperature_red_critical_zone():
    assert check_threshold(SensorType.TEMPERATURE, 80.1) == Severity.RED
    assert check_threshold(SensorType.TEMPERATURE, 120.0) == Severity.RED

# --- Load Tests ---

def test_load_green_safe_zone():
    assert check_threshold(SensorType.LOAD, 40.0) == Severity.GREEN
    assert check_threshold(SensorType.LOAD, 74.9) == Severity.GREEN

def test_load_yellow_warning_zone():
    # 75 to 90
    assert check_threshold(SensorType.LOAD, 75.0) == Severity.YELLOW
    assert check_threshold(SensorType.LOAD, 85.0) == Severity.YELLOW
    assert check_threshold(SensorType.LOAD, 90.0) == Severity.YELLOW

def test_load_red_critical_zone():
    assert check_threshold(SensorType.LOAD, 90.1) == Severity.RED
    assert check_threshold(SensorType.LOAD, 110.0) == Severity.RED
