from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from main import Hub, Connection, ZoneType

class InvalidFileError(Exception):
    def __init__(self, detail: Optional[str] = None) -> None:
        base = "The file you are using to represent the network of drones is invalid."
        message = f"{base}\n{detail}" if detail else base
        super().__init__(message)


class Config:
    def __init__(self) -> None:
        self.nb_drones:   int              = 0
        self.start_hub:   Hub              = None
        self.end_hub:     Hub              = None
        self.hubs:        List[Hub]        = []
        self.connections: List[Connection] = []

    def __str__(self) -> str:
        hubs_str = "\n".join(str(x) for x in self.hubs)
        conn_str = "\n".join(str(x) for x in self.connections)
        return (
                f"nb_drones: {self.nb_drones}\n"
                f"start_hub: {self.start_hub}\n"
                f"end_hub: {self.end_hub}\n"
                f"hubs: \n{hubs_str}\n"
                f"connections: \n{conn_str}"
                )


class FileParser:
    class LineType(Enum):
        NB_DRONES  = 1
        START_HUB  = 2
        END_HUB    = 3
        HUB        = 4
        CONNECTION = 5

    PREFIX_MAP: Dict[str, "FileParser.LineType"] = {
        "nb_drones":  LineType.NB_DRONES,
        "start_hub":  LineType.START_HUB,
        "end_hub":    LineType.END_HUB,
        "hub":        LineType.HUB,
        "connection": LineType.CONNECTION,
    }

    def __init__(self, file: Any) -> None:
        self.file   = file
        self.config = Config()
        self.seen: Dict[str, Optional[int]] = {
            "nb_drones": None,
            "start_hub": None,
            "end_hub":   None,
        }

    def split_meta(self, text: str) -> Tuple[str, Dict[str, str]]:
        if "[" not in text:
            return text.strip(), {}
        body, _, meta_block = text.partition("[")
        meta_block = meta_block.rstrip("]")
        kv = {}
        for part in meta_block.split():
            if "=" in part:
                k, _, v = part.partition("=")
                kv[k.strip()] = v.strip()
        return body.strip(), kv

    def parse_hub_line(self, line: str, lineno: int) -> Hub:
        _, _, rest = line.partition(":")
        body, meta = self.split_meta(rest)
        tokens = body.split()
        if len(tokens) < 3:
            raise InvalidFileError(
                f"    Line {lineno}: Hub line requires '<name> <x> <y>'.\n"
                f"            '{line}'"
            )
        name = tokens[0]
        try:
            x, y = int(tokens[1]), int(tokens[2])
        except ValueError:
            raise InvalidFileError(
                f"    Line {lineno}: Hub coordinates must be integers.\n"
                f"            '{line}'"
            )
        zone_raw = meta.get("zone", ZoneType.NORMAL.value)
        try:
            zone = ZoneType(zone_raw)
        except ValueError:
            raise InvalidFileError(
                f"    Line {lineno}: Unknown zone type {zone_raw!r}.\n"
                f"            '{line}'"
            )
        color      = meta.get("color")
        max_drones = int(meta.get("max_drones", 1))
        return Hub(name=name, x=x, y=y, zone=zone, color=color, max_drones=max_drones)

    def check_duplicate(self, key: str, lineno: int) -> None:
        if self.seen.get(key) is not None:
            raise InvalidFileError(
                f"    Line {lineno}: Duplicate '{key}' declaration "
                f"(first seen on line {self.seen[key]})."
            )
        self.seen[key] = lineno

    def parse(self) -> Config:
        first_content_line = True

        for lineno, raw in enumerate(self.file, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if first_content_line:
                prefix, sep, _ = line.partition(":")
                if not sep:
                    raise InvalidFileError(
                        f"    Line {lineno}: Expected 'nb_drones: <number>' as the first line.\n"
                        f"            '{line}'\n"
                        f"             {' ' * 9}^"
                    )
                if prefix.strip() != "nb_drones":
                    raise InvalidFileError(
                        f"    Line {lineno}: Expected 'nb_drones: <number>' as the first line.\n"
                        f"            '{line}'\n"
                        f"             ^"
                    )
                first_content_line = False

            prefix = line.split(":")[0].strip()
            lt = self.PREFIX_MAP.get(prefix)
            if lt is None:
                raise InvalidFileError(
                    f"    Line {lineno}: {prefix!r} is not a valid line prefix.\n"
                    f"            '{line}'\n"
                    f"             ^"
                )

            if lt == self.LineType.NB_DRONES:
                self.check_duplicate("nb_drones", lineno)
                _, _, rest = line.partition(":")
                try:
                    self.config.nb_drones = int(rest.strip())
                except ValueError:
                    raise InvalidFileError(
                        f"    Line {lineno}: 'nb_drones' value must be an integer.\n"
                        f"            '{line}'"
                    )

            elif lt == self.LineType.START_HUB:
                self.check_duplicate("start_hub", lineno)
                self.config.start_hub = self.parse_hub_line(line, lineno)

            elif lt == self.LineType.END_HUB:
                self.check_duplicate("end_hub", lineno)
                self.config.end_hub = self.parse_hub_line(line, lineno)

            elif lt == self.LineType.HUB:
                self.config.hubs.append(self.parse_hub_line(line, lineno))

            elif lt == self.LineType.CONNECTION:
                _, _, rest = line.partition(":")
                body, meta = self.split_meta(rest.strip())
                parts = body.strip().split("-")
                if len(parts) != 2 or not parts[0] or not parts[1]:
                    raise InvalidFileError(
                        f"    Line {lineno}: Connection must be '<nameA>-<nameB>'.\n"
                        f"            '{line}'"
                    )
                capacity = int(meta.get("max_link_capacity", 1))
                self.config.connections.append(
                    Connection(parts[0].strip(), parts[1].strip(), capacity)
                )

        if self.seen["nb_drones"] is None:
            raise InvalidFileError("Missing required 'nb_drones' declaration.")
        if self.seen["start_hub"] is None:
            raise InvalidFileError("Missing required 'start_hub' declaration.")
        if self.seen["end_hub"] is None:
            raise InvalidFileError("Missing required 'end_hub' declaration.")

        return self.config
