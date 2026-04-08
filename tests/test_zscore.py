import math
from models.enums import Severity
from services.zscore import compute_zscore, evaluate_zscore_severity
from config import ZSCORE_WARN_THRESHOLD, ZSCORE_CRIT_THRESHOLD

class TestZScoreComputation:

    def test_not_enough_data(self):
        # Array length < 5 should gracefully return 0.0
        assert compute_zscore(50.0, [50.0, 51.0, 49.0]) == 0.0
        assert compute_zscore(50.0, []) == 0.0

    def test_normal_calculation(self):
        # Mean = 5.0, Stdev approx = 2.138
        recent = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        val = 9.0
        # Expected absolute deviation: |9 - 5.0| / 2.138 = 1.87
        z = compute_zscore(val, recent)
        assert abs(z - 1.87) < 0.1

    def test_zero_variance_identical_matching(self):
        # All readings are 100.0, and the new value is 100.0
        recent = [100.0, 100.0, 100.0, 100.0, 100.0]
        # Should return 0.0 safely instead of ZeroDivisionError
        assert compute_zscore(100.0, recent) == 0.0

    def test_zero_variance_with_spike(self):
        # All recent readings are flat 100.0, but new value spikes
        recent = [100.0, 100.0, 100.0, 100.0, 100.0]
        # Mathematical infinite anomaly due to absolute baseline deviation
        z = compute_zscore(150.0, recent)
        assert z == float('inf')


class TestZScoreSeverityEvaluation:

    def test_green_evaluation_normal_bands(self):
        sev, is_anomaly = evaluate_zscore_severity(0.0)
        assert sev == Severity.GREEN
        assert is_anomaly == False
        
        sev, is_anomaly = evaluate_zscore_severity(2.9)
        assert sev == Severity.GREEN
        assert is_anomaly == False

    def test_yellow_evaluation_warning_bounds(self):
        sev, is_anomaly = evaluate_zscore_severity(A := ZSCORE_WARN_THRESHOLD)
        assert sev == Severity.YELLOW
        assert is_anomaly == True
        
        sev, is_anomaly = evaluate_zscore_severity(4.9)
        assert sev == Severity.YELLOW
        assert is_anomaly == True

    def test_red_evaluation_critical_bounds(self):
        sev, is_anomaly = evaluate_zscore_severity(A := ZSCORE_CRIT_THRESHOLD)
        assert sev == Severity.RED
        assert is_anomaly == True
        
        sev, is_anomaly = evaluate_zscore_severity(100.0)
        assert sev == Severity.RED
        assert is_anomaly == True

    def test_inf_anomaly_panic_evaluation(self):
        sev, is_anomaly = evaluate_zscore_severity(float('inf'))
        assert sev == Severity.RED
        assert is_anomaly == True
