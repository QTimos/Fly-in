from typing import Optional
from enum import Enum

class ZoneType(str, Enum):
    NORMAL     = "normal"
    BLOCKED    = "blocked"
    RESTRICTED = "restricted"
    PRIORITY   = "priority"


class Hub:
    def __init__(self, name: str, x: int, y: int, zone: ZoneType = ZoneType.NORMAL,
                 color: Optional[str] = None, max_drones: int = 1) -> None:
        self.name       = name
        self.x          = x
        self.y          = y
        self.zone       = zone
        self.color      = color
        self.max_drones = max_drones

    def __str__(self) -> str:
        return (
                "{\n"
                f"  {self.name}\n"
                f"  {self.x}\n"
                f"  {self.y}\n"
                f"  {self.zone}\n"
                f"  {self.color}\n"
                f"  {self.max_drones}\n"
                "}\n"
                )


class Connection:
    def __init__(self, a: str, b: str, max_link_capacity: int = 1) -> None:
        self.a                 = a
        self.b                 = b
        self.max_link_capacity = max_link_capacity

    def __str__(self) -> str:
        return (
                "{\n"
                f"  {self.a}\n"
                f"  {self.b}\n"
                f"  {self.max_link_capacity}\n"
                "}\n"
                )


def test_parsing() -> None:
    from parse import FileParser
    file_path = "01_linear_path.txt"
    with open(file_path) as file:
        parser = FileParser(file)
        config = parser.parse()
        print(config)

def main() -> None:
    pass

if __name__ == "__main__":
    test_parsing()
