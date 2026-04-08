import random
import time
import threading
from uuid import uuid4
from datetime import datetime
from models.sensor import Sensor
from models.reading import TelemetryReading
from models.enums import SensorType

# baseline normal values per sensor type
BASELINES = {
    SensorType.VOLTAGE:     220.0,
    SensorType.TEMPERATURE: 55.0,
    SensorType.LOAD:        50.0,
}

# normal noise standard deviation
NOISE_STD = {
    SensorType.VOLTAGE:     2.0,
    SensorType.TEMPERATURE: 1.5,
    SensorType.LOAD:        2.5,
}

# spike values that breach thresholds
SPIKE_VALUES = {
    SensorType.VOLTAGE:     random.choice([160.0, 260.0]),  # low or high critical
    SensorType.TEMPERATURE: 85.0,                            # above RED threshold
    SensorType.LOAD:        95.0,                            # above RED threshold
}

# drift state tracker per sensor
_drift_state: dict[str, dict] = {}


def _get_drift_state(sensor_id: str) -> dict:
    if sensor_id not in _drift_state:
        _drift_state[sensor_id] = {
            "active":    False,
            "step":      0,
            "direction": 1,
        }
    return _drift_state[sensor_id]


def inject_spike(sensor_type: SensorType) -> float:
    """Single sharp spike — immediate breach."""
    if sensor_type == SensorType.VOLTAGE:
        return random.choice([160.0, 260.0])
    elif sensor_type == SensorType.TEMPERATURE:
        return round(random.uniform(83.0, 90.0), 2)
    elif sensor_type == SensorType.LOAD:
        return round(random.uniform(91.0, 99.0), 2)


def inject_drift(sensor_type: SensorType, sensor_id: str, reading_index: int) -> float:
    """Slow climb over 10 readings toward a danger zone."""
    state = _get_drift_state(sensor_id)

    # start a new drift every 50 readings
    if reading_index % 50 == 0:
        state["active"]    = True
        state["step"]      = 0
        state["direction"] = random.choice([1, -1])

    if state["active"]:
        drift_amount = state["step"] * 2.0 * state["direction"]
        state["step"] += 1

        if state["step"] > 10:
            state["active"] = False  # drift ends after 10 steps

        return BASELINES[sensor_type] + drift_amount

    return None  # no drift active


def generate_reading(sensor: Sensor, reading_index: int) -> TelemetryReading:
    base  = BASELINES[sensor.type]
    noise = random.gauss(0, NOISE_STD[sensor.type])

    # priority 1 — spike (every 30 readings)
    if reading_index % 30 == 0:
        value = inject_spike(sensor.type)

    # priority 2 — sustained drift (every 50 readings, lasts 10 steps)
    else:
        drift_value = inject_drift(sensor.type, sensor.id, reading_index)
        if drift_value is not None:
            value = drift_value + random.gauss(0, 0.5)  # small noise on top of drift
        else:
            # priority 3 — normal reading
            value = base + noise

    return TelemetryReading(
        id=str(uuid4()),
        sensor_id=sensor.id,
        value=round(value, 2),
        timestamp=datetime.now(),
    )


class DataGenerator(threading.Thread):
    """
    Dedicated Background Polling Thread.
    Autonomously pumps generated data straight through the Python mathematics engine!
    """
    def __init__(self, store, engine):
        super().__init__(daemon=True) # Exits aggressively when Python exits
        self.store = store
        self.engine = engine
        self._running = False
        self.cycle_count = 0
        
    def start(self):
        self._running = True
        super().start()
        
    def stop(self):
        self._running = False
        
    def run(self):
        # 1. Discover all dynamic sensors straight from the Store
        with self.store.get_connection() as conn:
            sensors_data = conn.execute("SELECT * FROM sensors").fetchall()
            
        sensors = []
        for s_row in sensors_data:
            sensors.append(Sensor(
                id=s_row['id'],
                station_id=s_row['station_id'],
                type=SensorType(s_row['type']),
                unit=s_row['unit']
            ))
            
        # 2. Trigger infinite hardware pulse!
        while self._running:
            self.cycle_count += 1
            readings_batch = []
            
            for sens in sensors:
                # Mathematically spool raw numbers
                raw_reading = generate_reading(sens, self.cycle_count)
                # Ensure the engine filters them for limit logic overriding thresholds 
                processed = self.engine.process_reading(raw_reading, sens, self.store)
                readings_batch.append(processed)
                
            if readings_batch:
                self.store.save_readings_batch(readings_batch)
                
            time.sleep(2.0) # Sleep securely out-of-band simulating a 2s physical hardware burst