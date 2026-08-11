"""Tests for vcd.reader."""

import io
from textwrap import dedent

import pytest

from vcd.common import ScopeType, Timescale, TimescaleMagnitude, TimescaleUnit, VarType
from vcd.reader import (
    RealChange,
    ScalarChange,
    ScopeDecl,
    StringChange,
    TokenKind,
    VarDecl,
    VCDParseError,
    VectorChange,
    tokenize,
)


def test_parse_comment():
    tokens = tokenize(io.BytesIO(b"$comment hello $end"))
    token = next(tokens)
    assert token.comment == "hello"


def test_parse_multiline_comment():
    tokens = tokenize(io.BytesIO(b"$comment\nhello\nworld\n$end"))
    token = next(tokens)
    assert token.comment == "hello\nworld"


def test_parse_date():
    tokens = tokenize(io.BytesIO(b"$date\nnow!!! $end"))
    token = next(tokens)
    assert token.date == "now!!!"


def test_parse_date_with_bad_end():
    tokens = tokenize(io.BytesIO(b"$date\nnow!!!$end"))
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("2:6: ")


def test_parse_enddefinitions():
    tokens = tokenize(io.BytesIO(b"$comment hi $end $enddefinitions $end"))
    token = next(tokens)
    assert token.comment == "hi"
    token = next(tokens)
    assert token.kind == TokenKind.ENDDEFINITIONS


def test_parse_junk_in_enddefinitions():
    tokens = tokenize(io.BytesIO(b"$comment hi $end $enddefinitions $var $end"))
    token = next(tokens)
    assert token.comment == "hi"
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("1:35: Expected $end")


def test_parse_scope_decl():
    tokens = tokenize(io.BytesIO(b"$scope module foobar $end"))
    token = next(tokens)
    assert token.scope.type_.value == "module"
    assert token.scope.ident == "foobar"


def test_parse_scope_decl_with_escaped_identifier():
    tokens = tokenize(io.BytesIO(b"$scope module \\foo.bar\\ $end"))
    token = next(tokens)
    assert token.scope.type_.value == "module"
    assert token.scope.ident == "foo.bar\\"


@pytest.mark.parametrize(
    "ident",
    [
        "foobar",
        "SomeThing.MORE_STUFF_0",
        "scope_name(432)",  # cva6 core
        "genblock[3].mod",  # generate loop
        "uvm_phase::m_wait_for_pred",  # UVM
        "mem[0][1]",
        "weird-name#1",
    ],
)
def test_parse_scope_decl_idents(ident: str) -> None:
    vcd = f"$scope module {ident} $end".encode("ascii")
    token = next(tokenize(io.BytesIO(vcd)))
    assert token.scope == ScopeDecl(ScopeType.module, ident)


@pytest.mark.parametrize("scope_type", ScopeType)
def test_parse_scope_decl_types(scope_type: ScopeType) -> None:
    vcd = f"$scope {scope_type.value} foo $end".encode("ascii")
    token = next(tokenize(io.BytesIO(vcd)))
    assert token.scope == ScopeDecl(scope_type, "foo")


def test_parse_scope_decl_without_ident():
    # Verilator and other tools emit unnamed scopes.
    tokens = tokenize(io.BytesIO(b"$scope module $end"))
    token = next(tokens)
    assert token.scope == ScopeDecl(ScopeType.module, "")


def test_parse_scope_decl_with_escaped_end_ident():
    # An escaped identifier is opaque, so it may spell "$end".
    tokens = tokenize(io.BytesIO(b"$scope module \\$end $end"))
    token = next(tokens)
    assert token.scope == ScopeDecl(ScopeType.module, "$end")


def test_parse_var_decl():
    tokens = tokenize(io.BytesIO(b"$var integer 8 ! foo [17] $end"))
    token = next(tokens)
    assert token.var.type_ == VarType.integer
    assert token.var.ref_str == "foo[17]"


@pytest.mark.parametrize("var_type", VarType)
def test_parse_var_decl_types(var_type: VarType) -> None:
    vcd = f"$var {var_type.value} 8 ! foo $end".encode("ascii")
    token = next(tokenize(io.BytesIO(vcd)))
    assert token.var == VarDecl(var_type, 8, "!", "foo", None)


def test_parse_var_decl_with_dotted_ref():
    tokens = tokenize(io.BytesIO(b"$var real  1  aaaaa  SomeThing.MORE_STUFF_0  $end"))
    token = next(tokens)
    assert token.var.type_ == VarType.real
    assert token.var.ref_str == "SomeThing.MORE_STUFF_0"


def test_parse_var_decl_with_parens_in_ref_str():
    tokens = tokenize(io.BytesIO(b"$var integer 8 !! an(ident) $end"))
    token = next(tokens)
    assert token.var.ref_str == "an(ident)"


def test_parse_var_decl_from_standard():
    # The $var example given in IEEE 1800-2023 21.7.2.4, in which the bit
    # index is not separated from the reference by whitespace.
    tokens = tokenize(io.BytesIO(b"$var reg 32 (k accumulator[31:0] $end"))
    token = next(tokens)
    assert token.var == VarDecl(VarType.reg, 32, "(k", "accumulator", (31, 0))


@pytest.mark.parametrize(
    "ref, reference, bit_index",
    [
        ("foo", "foo", None),
        ("foo [17]", "foo", 17),
        ("foo[17]", "foo", 17),
        ("foo [7:0]", "foo", (7, 0)),
        ("foo[7:0]", "foo", (7, 0)),
        ("foo [ 3 : 1 ]", "foo", (3, 1)),
        ("foo[ 3 : 1 ]", "foo", (3, 1)),
        # A memory word, with and without a bit select, as emitted by verilator.
        ("mem_array[0]", "mem_array", 0),
        ("mem_array[0] [177:0]", "mem_array[0]", (177, 0)),
        ("mem_array[0][177:0]", "mem_array[0]", (177, 0)),
        ("varname [1423][SOMENAME][2]", "varname[1423][SOMENAME]", 2),
        ("foo[0][1][2][4:3]", "foo[0][1][2]", (4, 3)),
        # Nothing that fails to look like a bit index is split off.
        ("genblock[3].mod.sig", "genblock[3].mod.sig", None),
        ("uvm_pkg::thing", "uvm_pkg::thing", None),
        ("foo[x]", "foo[x]", None),
        ("foo[7:0:1]", "foo[7:0:1]", None),
        ("foo[]", "foo[]", None),
        ("[3]", "[3]", None),
        # Escaped identifiers are opaque, so only a following section counts.
        ("\\foo[7:0]", "foo[7:0]", None),
        ("\\mem[0] [7:0]", "mem[0]", (7, 0)),
    ],
)
def test_parse_var_decl_references(
    ref: str, reference: str, bit_index: None | int | tuple[int, int]
) -> None:
    vcd = f"$var wire 8 ! {ref} $end".encode("ascii")
    token = next(tokenize(io.BytesIO(vcd)))
    assert token.var == VarDecl(VarType.wire, 8, "!", reference, bit_index)


def test_parse_var_decl_without_ref():
    tokens = tokenize(io.BytesIO(b"$var wire 1 ! $end"))
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("1:15: Expected variable reference")


def test_parse_var_decl_with_junk_after_ref():
    tokens = tokenize(io.BytesIO(b"$var wire 1 ! foo bar $end"))
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("1:19: Expected $end")


def test_time_change():
    tokens = tokenize(io.BytesIO(b"#1234"))
    token = next(tokens)
    assert token.time_change == 1234


def test_scalar_change():
    tokens = tokenize(io.BytesIO(b'1!"$"'))
    token = next(tokens)
    assert token.scalar_change.id_code == '!"$"'
    assert token.scalar_change.value == "1"


def test_vector_change():
    tokens = tokenize(io.BytesIO(b"b1X1z   abc"))
    token = next(tokens)
    assert token.vector_change.id_code == "abc"
    assert token.vector_change.value == "1X1z"


def test_empty_vector_change() -> None:
    # GHDL emits `b !` for zero-width variables; the empty value is zero.
    tokens = tokenize(io.BytesIO(b"b !"))
    token = next(tokens)
    assert token.vector_change == VectorChange("!", 0)


@pytest.mark.parametrize("value", "01xXzZuUwWhHlL-")
def test_scalar_change_states(value: str) -> None:
    # In addition to the IEEE 1800 four-state values, VHDL simulators
    # such as GHDL emit nine-state std_logic values.
    tokens = tokenize(io.BytesIO(f"{value}!".encode("ascii")))
    token = next(tokens)
    assert token.scalar_change == ScalarChange("!", value)


def test_nine_state_vector_change() -> None:
    # GHDL dumps uninitialized std_logic vectors as `bUUUU`.
    tokens = tokenize(io.BytesIO(b"bUUUU !"))
    token = next(tokens)
    assert token.vector_change == VectorChange("!", "UUUU")


def test_all_states_vector_change() -> None:
    tokens = tokenize(io.BytesIO(b"b01xXzZuUwWhHlL- !"))
    token = next(tokens)
    assert token.vector_change == VectorChange("!", "01xXzZuUwWhHlL-")


def test_invalid_vector_change() -> None:
    tokens = tokenize(io.BytesIO(b"bG !"))
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("1:2: Expected vector value")


# The following tests exercise constructs observed in real-world VCD files
# collected in the test corpus of wellen (https://github.com/ekiwi/wellen),
# a Rust waveform parsing library. Each test notes the tool that emits the
# construct in question.


def test_id_code_starting_with_hash() -> None:
    # An id code may start with '#' even though '#' also introduces time
    # change tokens; the scalar value and id code are not separated.
    tokens = tokenize(io.BytesIO(b"1#2!"))
    token = next(tokens)
    assert token.scalar_change == ScalarChange("#2!", "1")


def test_id_code_of_punctuation() -> None:
    tokens = tokenize(io.BytesIO(b'x(i"'))
    token = next(tokens)
    assert token.scalar_change == ScalarChange('(i"', "x")


def test_var_decl_reference_starting_with_digit() -> None:
    # Some SystemVerilog simulators emit synthetic names such as "598.tmp".
    tokens = tokenize(io.BytesIO(b"$var wire 104 8 598.tmp $end"))
    token = next(tokens)
    assert token.var == VarDecl(VarType.wire, 104, "8", "598.tmp", None)


def test_multiline_declarations() -> None:
    # Aldec and ModelSim spread declarations over multiple lines.
    vcd = b"$timescale\n\t1ns\n$end\n$scope module tb $end"
    tokens = tokenize(io.BytesIO(vcd))
    assert next(tokens).timescale == Timescale(
        TimescaleMagnitude.one, TimescaleUnit.nanosecond
    )
    assert next(tokens).scope == ScopeDecl(ScopeType.module, "tb")


def test_comment_between_var_decls() -> None:
    # ModelSim may interleave $comment declarations with $var declarations.
    vcd = b'$var reg 1 ! clk $end $comment foo $end $var reg 1 " reset $end'
    tokens = tokenize(io.BytesIO(vcd))
    assert next(tokens).var == VarDecl(VarType.reg, 1, "!", "clk", None)
    assert next(tokens).comment == "foo"
    assert next(tokens).var == VarDecl(VarType.reg, 1, '"', "reset", None)


def test_duplicate_id_codes() -> None:
    # An id code may be shared by multiple variables, aliasing one value
    # change to all of them.
    vcd = b"$var wire 1 ! clk $end $var wire 1 ! clock $end"
    tokens = tokenize(io.BytesIO(vcd))
    assert next(tokens).var.id_code == "!"
    assert next(tokens).var.id_code == "!"


def test_scalar_change_with_ws_before_id_code() -> None:
    # A scalar value must be immediately followed by its id code.
    tokens = tokenize(io.BytesIO(b"1 $"))
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("1:2: Expected id code")


def test_unknown_keyword() -> None:
    tokens = tokenize(io.BytesIO(b"$crash\n$version foo $end"))
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("2:1: invalid keyword $crash")


def test_fractional_time_change() -> None:
    # Times are integral; a nonzero fractional part cannot be represented.
    tokens = tokenize(io.BytesIO(b"#3.2\n0!"))
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("1:4: Expected zero fraction in time change")


def test_integral_float_time_change() -> None:
    # Migen emits float time changes with zero fractional parts, e.g. "#3.0".
    tokens = tokenize(io.BytesIO(b"#3.0\n0!"))
    assert next(tokens).time_change == 3
    assert next(tokens).scalar_change == ScalarChange("!", "0")


def test_bare_fraction_time_change() -> None:
    tokens = tokenize(io.BytesIO(b"#3.\n0!"))
    assert next(tokens).time_change == 3
    assert next(tokens).scalar_change == ScalarChange("!", "0")


def test_nonstandard_timescale_magnitude() -> None:
    # Only magnitudes 1, 10, and 100 are valid, but magnitudes such as
    # "244" have been observed in the wild.
    tokens = tokenize(io.BytesIO(b"$timescale 244 ns $end"))
    with pytest.raises(VCDParseError) as e:
        _ = next(tokens)
    assert str(e.value).startswith("1:15: Invalid $timescale magnitude: 244")


@pytest.mark.parametrize("ident", ["$unit", "$ivl_for_loop0"])
def test_scope_ident_starting_with_dollar(ident: str) -> None:
    # VCS names the SystemVerilog compilation-unit scope "$unit"; Icarus
    # Verilog emits synthetic scopes such as "$ivl_for_loop0".
    vcd = f"$scope module {ident} $end".encode("ascii")
    token = next(tokenize(io.BytesIO(vcd)))
    assert token.scope == ScopeDecl(ScopeType.module, ident)


def test_var_decl_reference_starting_with_dollar() -> None:
    # Amaranth and Yosys emit synthetic variable names such as "$signal".
    tokens = tokenize(io.BytesIO(b"$var wire 32 # $signal $end"))
    token = next(tokens)
    assert token.var == VarDecl(VarType.wire, 32, "#", "$signal", None)


def test_attr_declarations() -> None:
    # GTKWave's fst2vcd and nvc extend VCD with $attrbegin/$attrend
    # declarations carrying FST-style attributes.
    vcd = (
        b"$attrbegin misc 03 /src/tb.vhdl 1 $end\n"
        b"$attrbegin misc 02 STD_LOGIC 1030 $end\n"
        b"$var logic 1 ! clk $end\n"
        b"$attrend $end\n"
    )
    tokens = tokenize(io.BytesIO(vcd))
    assert next(tokens).attr == "misc 03 /src/tb.vhdl 1"
    assert next(tokens).attr == "misc 02 STD_LOGIC 1030"
    assert next(tokens).var == VarDecl(VarType.logic, 1, "!", "clk", None)
    assert next(tokens).kind is TokenKind.ATTREND


@pytest.mark.parametrize("buf_size", range(1, 400))
def test_comprehensive(buf_size: int) -> None:
    vcd = """\
        $comment Test VCD $end
        $date the present day $end
        $timescale 10 ps $end
        $scope module alpha $end
        $scope fork beta $end
        $var wire 1  ! a_scalar $end
        $var integer 8 " b_vector $end
        $upscope $end
        $var real 64 # c_real $end
        $var string 1 $ d_string $end
        $var wire 8 % e_vector [7:0] $end
        $var reg 178 & mem_array[0] [177:0] $end
        $var wire 4 ' f_vector[ 3 : 1 ] $end
        $upscope $end
        $enddefinitions $end
        #0
        $dumpvars
        1!
        b1010 "
        r12.34 #
        shello $
        $end
        #17
        0!
        #42
        b1zzz "
        l!
        bU-wl "
        #50.0
        b &
        r1e-10 #
        #999
        sbye $
        $comment
        Fin.
        $end

        """
    tokens = tokenize(io.BytesIO(dedent(vcd).encode("ascii")), buf_size)
    assert next(tokens).comment == "Test VCD"
    assert next(tokens).date == "the present day"
    assert next(tokens).timescale == Timescale(
        TimescaleMagnitude.ten, TimescaleUnit.picosecond
    )
    assert next(tokens).scope == ScopeDecl(ScopeType.module, "alpha")
    assert next(tokens).scope == ScopeDecl(ScopeType.fork, "beta")
    assert next(tokens).var == VarDecl(VarType.wire, 1, "!", "a_scalar", None)
    assert next(tokens).var == VarDecl(VarType.integer, 8, '"', "b_vector", None)
    assert next(tokens).kind is TokenKind.UPSCOPE
    assert next(tokens).var == VarDecl(VarType.real, 64, "#", "c_real", None)
    assert next(tokens).var == VarDecl(VarType.string, 1, "$", "d_string", None)
    assert next(tokens).var == VarDecl(VarType.wire, 8, "%", "e_vector", (7, 0))
    assert next(tokens).var == VarDecl(VarType.reg, 178, "&", "mem_array[0]", (177, 0))
    assert next(tokens).var == VarDecl(VarType.wire, 4, "'", "f_vector", (3, 1))
    assert next(tokens).kind is TokenKind.UPSCOPE
    assert next(tokens).kind is TokenKind.ENDDEFINITIONS
    assert next(tokens).time_change == 0
    assert next(tokens).kind is TokenKind.DUMPVARS
    assert next(tokens).scalar_change == ScalarChange("!", "1")
    assert next(tokens).vector_change == VectorChange('"', 10)
    assert next(tokens).real_change == RealChange("#", 12.34)
    assert next(tokens).string_change == StringChange("$", "hello")
    assert next(tokens).kind is TokenKind.END
    assert next(tokens).time_change == 17
    assert next(tokens).scalar_change == ScalarChange("!", "0")
    assert next(tokens).time_change == 42
    assert next(tokens).vector_change == VectorChange('"', "1zzz")
    assert next(tokens).scalar_change == ScalarChange("!", "l")
    assert next(tokens).vector_change == VectorChange('"', "U-wl")
    assert next(tokens).time_change == 50
    assert next(tokens).vector_change == VectorChange("&", 0)
    assert next(tokens).real_change == RealChange("#", 1e-10)
    assert next(tokens).time_change == 999
    assert next(tokens).string_change == StringChange("$", "bye")
    assert next(tokens).comment == "Fin."
    with pytest.raises(StopIteration):
        _ = next(tokens)
