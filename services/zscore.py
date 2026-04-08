import statistics
import logging
from typing import List, Tuple
from models.enums import Severity
from config import ZSCORE_WARN_THRESHOLD, ZSCORE_CRIT_THRESHOLD

logger = logging.getLogger(__name__)

def compute_zscore(value: float, recent_readings: List[float]) -> float:
    """
    Computes the absolute Z-score of a value against a rolling window of recent readings.
    Mathematically represents how many standard deviations a metric deviates from its moving average.
    """
    # Require a minimum statistical sample size to avoid false standard deviations
    if not recent_readings or len(recent_readings) < 5:
        return 0.0

    try:
        mean = statistics.mean(recent_readings)
        std  = statistics.stdev(recent_readings)

        # Prevent division by zero if all recent readings were exactly identical
        if std == 0.0:
            # If the value perfectly matches the static window, z-score is 0. 
            # Otherwise, the sudden shift is an infinitely high mathematical anomaly.
            return 0.0 if value == mean else float('inf')

        return abs(value - mean) / std
        
    except Exception as e:
        logger.warning(f"Failed to compute z-score: {e}")
        return 0.0

def evaluate_zscore_severity(zscore: float) -> Tuple[Severity, bool]:
    """
    Translates a statistical Z-score into a GridWatch Severity and establishes 
    the boolean Anomaly Flag based on the exact threshold configurations.
    
    Warning limit: Z > 3.0
    Critical limit: Z > 5.0
    """
    try:
        # Handle the infinitely high anomaly edge case safely
        if zscore == float('inf') or zscore >= ZSCORE_CRIT_THRESHOLD:
            return Severity.RED, True
            
        if zscore >= ZSCORE_WARN_THRESHOLD:
            return Severity.YELLOW, True
            
    except TypeError:
        pass
        
    # Standard variance band
    return Severity.GREEN, False