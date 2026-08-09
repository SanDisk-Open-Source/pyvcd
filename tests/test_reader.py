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
        next(tokens)
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
        next(tokens)
    assert e.value.args[0].startswith("1:35: Expected $end")


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
def test_parse_scope_decl_idents(ident):
    vcd = f"$scope module {ident} $end".encode("ascii")
    token = next(tokenize(io.BytesIO(vcd)))
    assert token.scope == ScopeDecl(ScopeType.module, ident)


def test_parse_scope_decl_without_ident():
    tokens = tokenize(io.BytesIO(b"$scope module $end"))
    with pytest.raises(VCDParseError) as e:
        next(tokens)
    assert e.value.args[0].startswith("1:15: Expected scope identifier")


def test_parse_var_decl():
    tokens = tokenize(io.BytesIO(b"$var integer 8 ! foo [17] $end"))
    token = next(tokens)
    assert token.var.type_ == VarType.integer
    assert token.var.ref_str == "foo[17]"


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
def test_parse_var_decl_references(ref, reference, bit_index):
    vcd = f"$var wire 8 ! {ref} $end".encode("ascii")
    token = next(tokenize(io.BytesIO(vcd)))
    assert token.var == VarDecl(VarType.wire, 8, "!", reference, bit_index)


def test_parse_var_decl_without_ref():
    tokens = tokenize(io.BytesIO(b"$var wire 1 ! $end"))
    with pytest.raises(VCDParseError) as e:
        next(tokens)
    assert e.value.args[0].startswith("1:15: Expected variable reference")


def test_parse_var_decl_with_junk_after_ref():
    tokens = tokenize(io.BytesIO(b"$var wire 1 ! foo bar $end"))
    with pytest.raises(VCDParseError) as e:
        next(tokens)
    assert e.value.args[0].startswith("1:19: Expected $end")


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


@pytest.mark.parametrize("buf_size", range(1, 400))
def test_comprehensive(buf_size):
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
        #50
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
    assert next(tokens).time_change == 50
    assert next(tokens).real_change == RealChange("#", 1e-10)
    assert next(tokens).time_change == 999
    assert next(tokens).string_change == StringChange("$", "bye")
    assert next(tokens).comment == "Fin."
    with pytest.raises(StopIteration):
        next(tokens)
