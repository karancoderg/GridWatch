from models.sensor import Sensor
from models.enums import SensorType, Severity
from models.reading import TelemetryReading
from data.generator import generate_reading, BASELINES, NOISE_STD

# helper to create a dummy sensor
def make_sensor(sensor_type: SensorType) -> Sensor:
    return Sensor(
        id=f"sensor_{sensor_type.value}",
        station_id="station_1",
        type=sensor_type,
        unit="V" if sensor_type == SensorType.VOLTAGE else "%"
    )


# --- return type tests ---

def test_generate_reading_returns_telemetry_reading():
    sensor = make_sensor(SensorType.VOLTAGE)
    reading = generate_reading(sensor, reading_index=1)
    assert isinstance(reading, TelemetryReading)

def test_generate_reading_has_correct_sensor_id():
    sensor = make_sensor(SensorType.VOLTAGE)
    reading = generate_reading(sensor, reading_index=1)
    assert reading.sensor_id == sensor.id

def test_generate_reading_has_timestamp():
    sensor = make_sensor(SensorType.TEMPERATURE)
    reading = generate_reading(sensor, reading_index=1)
    assert reading.timestamp is not None

def test_generate_reading_value_is_rounded():
    sensor = make_sensor(SensorType.LOAD)
    reading = generate_reading(sensor, reading_index=1)
    assert reading.value == round(reading.value, 2)


# --- normal reading tests ---

def test_normal_reading_close_to_baseline():
    sensor = make_sensor(SensorType.VOLTAGE)
    # index 1 — not a spike (not % 30 == 0), not a drift (not % 50 == 0)
    reading = generate_reading(sensor, reading_index=1)
    baseline = BASELINES[SensorType.VOLTAGE]
    assert abs(reading.value - baseline) < 20  # within reasonable range

def test_normal_temperature_close_to_baseline():
    sensor = make_sensor(SensorType.TEMPERATURE)
    reading = generate_reading(sensor, reading_index=1)
    baseline = BASELINES[SensorType.TEMPERATURE]
    assert abs(reading.value - baseline) < 15


# --- spike tests ---

def test_spike_injected_at_index_30():
    sensor = make_sensor(SensorType.VOLTAGE)
    reading = generate_reading(sensor, reading_index=30)
    baseline = BASELINES[SensorType.VOLTAGE]
    # spike should be far from baseline
    assert abs(reading.value - baseline) > 10

def test_spike_injected_at_index_60():
    sensor = make_sensor(SensorType.TEMPERATURE)
    reading = generate_reading(sensor, reading_index=60)
    baseline = BASELINES[SensorType.TEMPERATURE]
    assert abs(reading.value - baseline) > 10

def test_voltage_spike_outside_safe_range():
    sensor = make_sensor(SensorType.VOLTAGE)
    reading = generate_reading(sensor, reading_index=30)
    # voltage spike should be either very low or very high
    assert reading.value < 185 or reading.value > 250

def test_temperature_spike_above_red_threshold():
    sensor = make_sensor(SensorType.TEMPERATURE)
    reading = generate_reading(sensor, reading_index=30)
    assert reading.value > 80

def test_load_spike_above_red_threshold():
    sensor = make_sensor(SensorType.LOAD)
    reading = generate_reading(sensor, reading_index=30)
    assert reading.value > 90


# --- drift tests ---

def test_drift_starts_at_index_50():
    sensor = make_sensor(SensorType.VOLTAGE)
    reading = generate_reading(sensor, reading_index=50)
    # at drift start step=0 so value is close to baseline + small noise
    baseline = BASELINES[SensorType.VOLTAGE]
    assert abs(reading.value - baseline) < 10

def test_drift_increases_over_steps():
    sensor = make_sensor(SensorType.TEMPERATURE)
    # trigger drift start
    generate_reading(sensor, reading_index=50)
    # read a few steps into the drift
    readings = [generate_reading(sensor, reading_index=50 + i) for i in range(1, 8)]
    values = [r.value for r in readings]
    # values should not all be the same (drift is changing)
    assert len(set(values)) > 1


# --- default severity tests ---

def test_default_severity_is_green():
    sensor = make_sensor(SensorType.VOLTAGE)
    reading = generate_reading(sensor, reading_index=1)
    assert reading.severity == Severity.GREEN

def test_default_is_anomaly_is_false():
    sensor = make_sensor(SensorType.VOLTAGE)
    reading = generate_reading(sensor, reading_index=1)
    assert reading.is_anomaly == False