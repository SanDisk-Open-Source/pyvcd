"""Custom test fixtures for pyvcd."""

from __future__ import annotations

import io
from collections.abc import Iterator

import pytest

from vcd.gtkw import GTKWSave


@pytest.fixture
def gtkw() -> Iterator[GTKWSave]:
    sio = io.StringIO()
    gtkw = GTKWSave(sio)
    try:
        yield gtkw
    finally:
        sio.close()
