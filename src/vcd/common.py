from __future__ import annotations

import sys
from enum import Enum
from typing import NamedTuple

# The checker is configured for the oldest supported version, so it sees only
# one side of this.
if sys.version_info >= (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


class ScopeType(Enum):
    """Valid VCD scope types."""

    begin = "begin"
    fork = "fork"
    function = "function"
    module = "module"
    task = "task"


class VarType(Enum):
    """Valid VCD variable types."""

    event = "event"
    integer = "integer"
    parameter = "parameter"
    real = "real"
    realtime = "realtime"
    reg = "reg"
    supply0 = "supply0"
    supply1 = "supply1"
    time = "time"
    tri = "tri"
    triand = "triand"
    trior = "trior"
    trireg = "trireg"
    tri0 = "tri0"
    tri1 = "tri1"
    wand = "wand"
    wire = "wire"
    wor = "wor"
    string = "string"
    logic = "logic"

    @override
    def __str__(self) -> str:
        return self.value


class TimescaleMagnitude(Enum):
    """Valid timescale magnitudes."""

    one = 1
    ten = 10
    hundred = 100


class TimescaleUnit(Enum):
    """Valid timescale units."""

    second = "s"
    millisecond = "ms"
    microsecond = "us"
    nanosecond = "ns"
    picosecond = "ps"
    femtosecond = "fs"


class Timescale(NamedTuple):
    """Timescale magnitude and unit."""

    magnitude: TimescaleMagnitude
    unit: TimescaleUnit

    @classmethod
    def from_str(cls, s: str) -> Timescale:
        for unit in TimescaleUnit:
            if s == unit.value:
                mag = TimescaleMagnitude(1)
                break
        else:
            for mag in reversed(TimescaleMagnitude):
                mag_str = str(mag.value)
                if s.startswith(mag_str):
                    unit_str = s[len(mag_str) :].lstrip(" ")
                    unit = TimescaleUnit(unit_str)
                    break
            else:
                raise ValueError(f"Invalid timescale magnitude {s!r}")
        return Timescale(mag, unit)

    @override
    def __str__(self) -> str:
        return f"{self.magnitude.value} {self.unit.value}"
