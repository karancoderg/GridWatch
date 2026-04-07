@dataclass
class SubStation:
    id: str
    name: str
    location: str
    status: Severity = Severity.GREEN