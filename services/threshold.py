from models.enums import SensorType, Severity
from config import THRESHOLDS

def check_threshold(sensor_type: SensorType, value: float) -> Severity:
    """
    Evaluates telemetry readings against configured safe/warn/critical bounds.
    """
    if sensor_type not in THRESHOLDS:
        return Severity.GREEN

    bounds = THRESHOLDS[sensor_type]
    
    if sensor_type == SensorType.VOLTAGE:
        red_bounds = bounds[Severity.RED]
        # Critical < 185V or > 250V
        if value < red_bounds[1] or value > red_bounds[2]:
            return Severity.RED
            
        yellow_bounds = bounds[Severity.YELLOW]
        # Warning 185-200V or 240-250V
        if (yellow_bounds[0] <= value < yellow_bounds[1]) or \
           (yellow_bounds[2] < value <= yellow_bounds[3]):
            return Severity.YELLOW
            
    else: # TEMPERATURE and LOAD 
        red_threshold = bounds[Severity.RED][0]
        # Critical > 80C or > 90%
        if value > red_threshold:
            return Severity.RED
            
        yellow_low, yellow_high = bounds[Severity.YELLOW]
        # Warning 65-80C or 75-90%
        if yellow_low <= value <= yellow_high:
            return Severity.YELLOW

    # Within Safe constraints
    return Severity.GREEN