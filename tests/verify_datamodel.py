from models.station import SubStation
from models.enums import Severity

s = SubStation(id="s1", name="Station A", location="North Grid")
print(s.status)  # Severity.GREEN