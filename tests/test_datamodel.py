from models.station import SubStation
from models.enums import Severity

def test_substation_default_status():
    s = SubStation(id="s1", name="Station A", location="North Grid")
    assert s.status == Severity.GREEN