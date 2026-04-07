from dataclasses import dataclass
from models.enums import Severity
@dataclass
class SubStation:
    id: str
    name: str
    location: str
    status: Severity = Severity.GREEN