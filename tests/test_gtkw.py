"""Tests for vcd.gtkw module."""

import datetime
import os
import time
from io import StringIO
from pathlib import Path

import pytest

from vcd.gtkw import (
    GTKWColor,
    GTKWFlag,
    GTKWSave,
    decode_flags,
    make_translation_filter,
)


def gtkw_output(gtkw: GTKWSave) -> str:
    """Return what has been written to the save file so far."""
    assert isinstance(gtkw.file, StringIO)
    return gtkw.file.getvalue()


def test_decode_flags():
    assert decode_flags("@200") == ["blank"]
    assert decode_flags("200") == ["blank"]
    assert decode_flags(0x200) == ["blank"]
    assert decode_flags("@802023") == [
        "highlight",
        "hex",
        "rjustify",
        "ftranslated",
        "grp_begin",
    ]


def test_gtkw_comments(gtkw: GTKWSave):
    gtkw.comment("Hi", "abc", "def")
    lines = gtkw_output(gtkw).splitlines()
    assert lines == ["[*] Hi", "[*] abc", "[*] def"]


def test_gtkw_dumpfile(gtkw: GTKWSave):
    gtkw.dumpfile("/foo/bar")
    assert gtkw_output(gtkw) == '[dumpfile] "{}"\n'.format(os.path.abspath("/foo/bar"))


def test_gtkw_dumpfile_none(gtkw: GTKWSave):
    gtkw.dumpfile(None)
    assert gtkw_output(gtkw) == "[dumpfile] (null)\n"


def test_gtkw_dumpfile_noabspath(gtkw: GTKWSave):
    gtkw.dumpfile("foo", abspath=False)
    assert gtkw_output(gtkw) == '[dumpfile] "foo"\n'


def test_gtkw_dumpfile_mtime(gtkw: GTKWSave):
    with pytest.raises((FileNotFoundError, IOError)):
        gtkw.dumpfile_mtime(dump_path="InVaLiD")
    gtkw.dumpfile_mtime(mtime=1234567890.0)
    assert gtkw_output(gtkw) == '[dumpfile_mtime] "Fri Feb 13 23:31:30 2009"\n'


def test_gtkw_dumpfile_mtime_gmtime(gtkw: GTKWSave):
    with pytest.raises((FileNotFoundError, IOError)):
        gtkw.dumpfile_mtime(dump_path="InVaLiD")
    with pytest.raises(TypeError):
        gtkw.dumpfile_mtime(mtime="right now")  # pyright: ignore[reportArgumentType]
    gtkw.dumpfile_mtime(mtime=time.gmtime(1234567890.0))
    assert gtkw_output(gtkw) == '[dumpfile_mtime] "Fri Feb 13 23:31:30 2009"\n'


def test_gtkw_dumpfile_mtime_datetime(gtkw: GTKWSave):
    with pytest.raises((FileNotFoundError, IOError)):
        gtkw.dumpfile_mtime(dump_path="InVaLiD")
    gtkw.dumpfile_mtime(mtime=datetime.datetime(2009, 2, 13, 23, 31, 30))
    assert gtkw_output(gtkw) == '[dumpfile_mtime] "Fri Feb 13 23:31:30 2009"\n'


def test_gtkw_dumpfile_size(gtkw: GTKWSave):
    gtkw.dumpfile_size(1234)
    assert gtkw_output(gtkw) == "[dumpfile_size] 1234\n"


def test_gtkw_dumpfile_size_path(gtkw: GTKWSave, tmp_path: Path) -> None:
    dump_file = tmp_path / "test.dump"
    _ = dump_file.write_text("x")
    gtkw.dumpfile_size(dump_path=str(dump_file))
    assert gtkw_output(gtkw) == "[dumpfile_size] 1\n"


def test_gtkw_savefile_noname(gtkw: GTKWSave):
    gtkw.savefile()
    assert gtkw_output(gtkw) == "[savefile] (null)\n"


def test_gtkw_savefile_none():
    sio = StringIO()
    sio.name = "/some/path"
    gtkw = GTKWSave(sio)
    gtkw.savefile()
    assert sio.getvalue() == '[savefile] "{}"\n'.format(os.path.abspath("/some/path"))


def test_gtkw_savefile_path(gtkw: GTKWSave):
    gtkw.savefile("/foo/bar")
    assert gtkw_output(gtkw) == '[savefile] "{}"\n'.format(os.path.abspath("/foo/bar"))


def test_gtkw_savefile_noabs(gtkw: GTKWSave):
    gtkw.savefile("foo/bar", abspath=False)
    assert gtkw_output(gtkw) == '[savefile] "foo/bar"\n'


def test_gtkw_timestart_default(gtkw: GTKWSave):
    gtkw.timestart()
    assert gtkw_output(gtkw) == "[timestart] 0\n"


def test_gtkw_zoom_markers(gtkw: GTKWSave):
    gtkw.zoom_markers(marker=17, z=999)
    assert gtkw_output(gtkw) == "*0.000000 17" + (" -1" * 25) + " 999\n"


def test_gtkw_size(gtkw: GTKWSave):
    gtkw.size(123, 456)
    assert gtkw_output(gtkw) == "[size] 123 456\n"


def test_gtkw_pos(gtkw: GTKWSave):
    gtkw.pos(123, -1)
    assert gtkw_output(gtkw) == "[pos] 123 -1\n"


def test_gtkw_treeopen(gtkw: GTKWSave):
    gtkw.treeopen("a.b.")
    gtkw.treeopen("a.b.c")
    assert gtkw_output(gtkw).splitlines() == [
        "[treeopen] a.b.",
        "[treeopen] a.b.c.",
    ]  # '.' added


def test_gtkw_signals_width(gtkw: GTKWSave):
    gtkw.signals_width(1234)
    assert gtkw_output(gtkw) == "[signals_width] 1234\n"


def test_gtkw_sst_expanded(gtkw: GTKWSave):
    gtkw.sst_expanded(True)
    assert gtkw_output(gtkw) == "[sst_expanded] 1\n"


def test_gtkw_pattern_trace(gtkw: GTKWSave):
    gtkw.pattern_trace(False)
    assert gtkw_output(gtkw) == "[pattern_trace] 0\n"


def test_gtkw_group(gtkw: GTKWSave):
    with gtkw.group("mygroup"):
        gtkw.trace("a.b.c", alias="C", color=GTKWColor.yellow)
        gtkw.trace("a.b.d")

    lines = gtkw_output(gtkw).splitlines()
    assert lines == [
        "@800200",
        "-mygroup",
        "@22",
        "[color] 3",
        "+{C} a.b.c",
        "a.b.d",
        "@1000200",
        "-mygroup",
    ]


def test_gtkw_group_closed(gtkw: GTKWSave):
    with gtkw.group("mygroup", closed=True):
        gtkw.trace("a.b.c", alias="C", color=GTKWColor.yellow)
        gtkw.trace("a.b.d")

    lines = gtkw_output(gtkw).splitlines()
    assert lines == [
        "@c00200",
        "-mygroup",
        "@22",
        "[color] 3",
        "+{C} a.b.c",
        "a.b.d",
        "@1401200",
        "-mygroup",
    ]


def test_gtkw_group_highlight(gtkw: GTKWSave):
    with gtkw.group("mygroup", highlight=True):
        gtkw.trace("a.b.c", alias="C", color=GTKWColor.yellow)
        gtkw.trace("a.b.d")

    lines = gtkw_output(gtkw).splitlines()
    assert lines == [
        "@800201",
        "-mygroup",
        "@22",
        "[color] 3",
        "+{C} a.b.c",
        "a.b.d",
        "@1000201",
        "-mygroup",
    ]


def test_gtkw_blank(gtkw: GTKWSave):
    gtkw.blank()
    assert gtkw_output(gtkw) == "@200\n-\n"


def test_gtkw_blank_highlight(gtkw: GTKWSave):
    gtkw.blank(highlight=True)
    assert gtkw_output(gtkw) == "@201\n-\n"


def test_gtkw_blanks(gtkw: GTKWSave):
    gtkw.blank()
    gtkw.blank()
    gtkw.blank()
    assert gtkw_output(gtkw) == "@200\n-\n-\n-\n"


def test_gtkw_analog_extension(gtkw: GTKWSave):
    gtkw.trace("a.b.c", datafmt="real")
    gtkw.blank(analog_extend=True)

    lines = gtkw_output(gtkw).splitlines()
    assert lines == ["@40020", "a.b.c", "@20200", "-"]


def test_gtkw_labels(gtkw: GTKWSave):
    gtkw.blank("hi")
    gtkw.blank("ho")
    assert gtkw_output(gtkw) == "@200\n-hi\n-ho\n"


def test_gtkw_invalid_datafmt(gtkw: GTKWSave):
    with pytest.raises(ValueError):
        gtkw.trace("a.b.c", datafmt="InVaLiD")


def test_gtkw_trace_highlight(gtkw: GTKWSave):
    gtkw.trace("a.b.c", highlight=True, rjustify=False)
    assert gtkw_output(gtkw) == "@3\na.b.c\n"


def test_gtkw_trace_extraflags(gtkw: GTKWSave):
    gtkw.trace(
        "a.b.c",
        datafmt="real",
        extraflags=GTKWFlag.analog_step | GTKWFlag.analog_fullscale,
    )
    assert gtkw_output(gtkw) == "@c8020\na.b.c\n"


def test_gtkw_trace_extraflags_deprecation(gtkw: GTKWSave):
    with pytest.warns(DeprecationWarning):
        gtkw.trace(
            "a.b.c", datafmt="real", extraflags=["analog_step", "analog_fullscale"]
        )
    with pytest.warns(DeprecationWarning):
        gtkw.trace("a.b.c", datafmt="real", extraflags=None)


def test_gtkw_trace_color_deprecation(gtkw: GTKWSave):
    with pytest.warns(DeprecationWarning):
        gtkw.trace("a.b.c", color="blue")

    with pytest.warns(DeprecationWarning):
        gtkw.trace("d.e.f", color=7)

    assert gtkw_output(gtkw) == "\n".join(
        ["@22", "[color] 5", "a.b.c", "[color] 7", "d.e.f", ""]
    )


def test_gtkw_trace_filter_files(gtkw: GTKWSave):
    gtkw.trace("mod.a", translate_filter_file="filter1.txt")
    gtkw.trace("mod.b", translate_filter_file="filter2.txt")
    gtkw.trace("mod.c", translate_filter_file="filter1.txt")
    lines = gtkw_output(gtkw).splitlines()

    assert lines == [
        "@2022",
        "^1 filter1.txt",
        "mod.a",
        "^2 filter2.txt",
        "mod.b",
        "^1 filter1.txt",
        "mod.c",
    ]


def test_gtkw_trace_filter_proc(gtkw: GTKWSave):
    gtkw.trace("a.b.c", translate_filter_proc="filter.exe")
    assert gtkw_output(gtkw) == "@4022\n^>1 filter.exe\na.b.c\n"


def test_gtkw_trace_bits(gtkw: GTKWSave):
    name = "a.b.c[3:0]"
    with gtkw.trace_bits(name):
        gtkw.trace_bit(0, name, alias="bit0", color=GTKWColor.normal)
        gtkw.trace_bit(1, name, alias="bit1")
        gtkw.trace_bit(2, name, color=GTKWColor.yellow)
        gtkw.trace_bit(3, name)

    lines = gtkw_output(gtkw).splitlines()

    assert lines == [
        "@22",
        "a.b.c[3:0]",
        "@28",
        "[color] 0",
        "+{bit0} (0)a.b.c[3:0]",
        "+{bit1} (1)a.b.c[3:0]",
        "[color] 3",
        "(2)a.b.c[3:0]",
        "(3)a.b.c[3:0]",
        "@1001200",
        "-group_end",
    ]


def test_gtkw_trace_bits_highlight(gtkw: GTKWSave):
    name = "a.b.c[3:0]"
    with gtkw.trace_bits(name, highlight=True, rjustify=False):
        gtkw.trace_bit(0, name, alias="bit0", color=GTKWColor.normal)
        gtkw.trace_bit(1, name, alias="bit1")
        gtkw.trace_bit(2, name, color=GTKWColor.orange)
        gtkw.trace_bit(3, name)

    lines = gtkw_output(gtkw).splitlines()

    assert lines == [
        "@3",
        "a.b.c[3:0]",
        "@9",
        "[color] 0",
        "+{bit0} (0)a.b.c[3:0]",
        "+{bit1} (1)a.b.c[3:0]",
        "[color] 2",
        "(2)a.b.c[3:0]",
        "(3)a.b.c[3:0]",
        "@1001201",
        "-group_end",
    ]


def test_gtkw_trace_bits_extra(gtkw: GTKWSave):
    name = "a.b.c[1:0]"
    with gtkw.trace_bits(name, extraflags=GTKWFlag.invert):
        gtkw.trace_bit(0, name, alias="bit0", color=GTKWColor.cycle)
        gtkw.trace_bit(1, name, alias="bit1", color=GTKWColor.cycle)

    lines = gtkw_output(gtkw).splitlines()

    assert lines == [
        "@62",
        "a.b.c[1:0]",
        "@68",
        "[color] 1",
        "+{bit0} (0)a.b.c[1:0]",
        "[color] 2",
        "+{bit1} (1)a.b.c[1:0]",
        "@1001200",
        "-group_end",
    ]


def test_gtkw_trace_bits_extra_deprecations(gtkw: GTKWSave):
    name = "a.b.c[1:0]"
    with pytest.warns(DeprecationWarning):
        with gtkw.trace_bits(name, extraflags=["invert"]):
            gtkw.trace_bit(0, name, alias="bit0", color=GTKWColor.cycle)
            gtkw.trace_bit(1, name, alias="bit1", color=GTKWColor.cycle)

    with pytest.warns(DeprecationWarning):
        with gtkw.trace_bits(name, extraflags=None):
            gtkw.trace_bit(0, name, alias="bit0", color=GTKWColor.cycle)
            gtkw.trace_bit(1, name, alias="bit1", color=GTKWColor.cycle)


def test_gtkw_color_stack(gtkw: GTKWSave):
    gtkw.trace("a", color=GTKWColor.cycle)
    gtkw.trace("b", color=GTKWColor.cycle)
    with gtkw.group("mygroup"):
        gtkw.trace("x", color=GTKWColor.cycle)
        gtkw.trace("y", color=GTKWColor.cycle)
        gtkw.trace("z", color=GTKWColor.cycle)
    gtkw.trace("c", color=GTKWColor.cycle)
    gtkw.trace("d", color=GTKWColor.cycle)

    lines = gtkw_output(gtkw).splitlines()

    assert lines == [
        "@22",
        "[color] 1",
        "a",
        "[color] 2",
        "b",
        "@800200",
        "-mygroup",
        "@22",
        "[color] 1",
        "x",
        "[color] 2",
        "y",
        "[color] 3",
        "z",
        "@1000200",
        "-mygroup",
        "@22",
        "[color] 3",
        "c",
        "[color] 4",
        "d",
    ]


def test_xlate_filter():
    xlatef = make_translation_filter(
        size=8,
        translations=[
            (16, "Sixteen", "Magenta"),
            (32, "Thirty-two"),
            (-128, "Negative"),
            (255, "Two Five Five", "Blue"),
        ],
    )

    assert xlatef.splitlines() == [
        "10 ?Magenta?Sixteen",
        "20 Thirty-two",
        "80 Negative",
        "ff ?Blue?Two Five Five",
    ]


def test_xlate_filter_size():
    with pytest.raises(ValueError):
        # 8 does not fit in 3-bits.
        _ = make_translation_filter(
            size=3, datafmt="oct", translations=[(8, "Eight", "Red")]
        )


def test_xlate_filter_datafmt():
    with pytest.raises(ValueError):
        _ = make_translation_filter(
            size=8, datafmt="InVaLiD", translations=[(8, "Eight", "Red")]
        )


def test_xlate_filter_bin():
    xlatef = make_translation_filter(
        size=2, datafmt="bin", translations=[(0, "Zero"), (1, "One"), (2, "Two")]
    )

    assert xlatef.splitlines() == ["00 Zero", "01 One", "10 Two"]


def test_xlate_filter_decimal():
    xlatef = make_translation_filter(
        datafmt="dec",
        translations=[(1, "X"), (1234, "XXXX"), (123456789, "XXXXXXXXX")],
    )

    assert xlatef.splitlines() == ["1 X", "1234 XXXX", "123456789 XXXXXXXXX"]


def test_xlate_filter_ascii():
    xlatef = make_translation_filter(
        datafmt="ascii",
        translations=[
            ("a", "Aye"),
            ("+", "Plus", "Red"),
            ("!", "Bang"),
            (35, "Pound", "Blue"),
        ],
    )

    assert xlatef.splitlines() == ["a Aye", "+ ?Red?Plus", "! Bang", "# ?Blue?Pound"]


def test_xlate_filter_invalid_ascii():
    with pytest.raises(ValueError):
        _ = make_translation_filter(datafmt="ascii", translations=[("abc", "ABC")])

    with pytest.raises(TypeError):
        _ = make_translation_filter([(35.0, "Pound")], datafmt="ascii")  # pyright: ignore[reportArgumentType]


def test_xlate_filter_real():
    xlatef = make_translation_filter(
        datafmt="real",
        translations=[  # pyright: ignore[reportArgumentType]
            (123, "One two three"),
            (44.0, "Forty-four"),
            (1.23, "One point two three"),
            (-17.5, "Sub zero"),
        ],
    )

    assert xlatef.splitlines() == [
        "123 One two three",
        "44 Forty-four",
        "1.23 One point two three",
        "-17.5 Sub zero",
    ]
