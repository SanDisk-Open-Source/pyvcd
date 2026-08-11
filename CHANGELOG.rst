Changelog
=========

pyvcd-0.5.0 (2026-08-11)
------------------------
* Breaking changes:

  * Raise the minimum supported Python version to 3.10
  * Model `Timescale.magnitude` as a plain `int`. `TimescaleMagnitude` remains
    as an `IntEnum` whose members compare equal to their integer values, but
    code such as `timescale.magnitude.value` must become
    `timescale.magnitude`.

* Reader features, aligning `vcd.reader` with the corpus of real-world VCD
  files collected by the `wellen`__ waveform library:

  * Accept the nonstandard SystemVerilog and VHDL scope and variable types
    emitted by GHDL, nvc, Verilator, QuestaSim, and fst2vcd
  * Accept nine-state std_logic values, e.g. ``bUUUU``, in scalar and vector
    value changes
  * Accept empty vector values, e.g. ``b !``, emitted by GHDL for zero-width
    variables
  * Accept float time changes with zero fractional parts, e.g. ``#3.0``,
    emitted by Migen
  * Accept any positive integer timescale magnitude, not just 1, 10, and 100
  * Accept scope and variable names starting with ``$``, e.g. VCS's
    ``$unit``, as well as unnamed scopes
  * Tokenize the ``$attrbegin``/``$attrend`` attribute extension emitted by
    nvc and fst2vcd
  * Split possibly-negative bit indices, e.g. ``signal[2:-2]``, from variable
    references

  __ https://github.com/ekiwi/wellen

* Other features:

  * Add `bit_index` parameter to `VCDWriter.register_var()` for references
    such as ``mem[0]`` and fixed-point annotations such as ``signal[2:-2]``
    (#5, #37)
  * Accept nonstandard timescale magnitudes in `VCDWriter`, keeping the
    writer able to re-emit anything the reader accepts
  * Add nonstandard `as` (attosecond) and `zs` (zeptosecond) timescale units
  * Add `GTKWSave.trace_combined()` for combined vector traces, as created by
    GTKWave's Combine Down operation (#23)
  * Add `transaction_filter_proc` parameter to `GTKWSave.trace()`,
    `trace_bits()`, and `trace_combined()` for GTKWave transaction filter
    processes (#23)

* Repairs:

  * Raise `VCDParseError` instead of `ValueError` for vector value changes
    with no value digits
  * Correct the `GTKWSave.zoom_markers()` keyword annotation
  * Name the empty set of GTKWave trace flags `GTKWFlag.none`

* Development environment changes:

  * Manage the project, virtualenvs, and compatibility matrix with uv and
    tox-uv
  * Check types with basedpyright in addition to mypy

pyvcd-0.4.2 (2026-08-09)
------------------------
* fix: accept special characters in reader scope and variable names (#22, #35)
* fix: take a variable's bit index from the final bracketed section of its
  reference (#22)
* build: remove deprecated packaging metadata (#42)
* docs: official support for Python 3.14
* docs: cite IEEE 1800-2023 for the VCD specification
* docs: project moved back to the SanDisk-Open-Source organization

pyvcd-0.4.1 (2024-11-10)
------------------------
* feat: support escaped identifiers (#27)
* feat: add `VarType.logic` used by Verilator (#30)
* feat: make some `VCDReader` exceptions unchained
* docs: typo in `VarDecl.id_code` docstring (#34)
* docs: official support for Python 3.12 and 3.13
* test: fix dumpfile_mtime tests

pyvcd-0.4.0 (2023-05-16)
------------------------
* Drop official support for EOL Python 3.6 (#25)
* Add official support for Python 3.10 and 3.11
* Identifiers may have parens (#21)
* Repair typing issue in vcd.gtkw.decode_flags()
* Repair sphinx config warnings
* Build using `build` instead of executing setup.py
* Repair deprecated use of license_file in setup.cfg

pyvcd-0.3.0 (2021-09-28)
------------------------
* Add vcd.reader module for parsing VCD files
* Various repairs to vcd.gtkw docs
* Update setuptools and setuptools_scm requirements

pyvcd-0.2.4 (2020-12-15)
------------------------
* Escape special characters in (GTKWave) string vars (#17)
* Update package classifiers for for Python 3.9 support

pyvcd-0.2.3 (2020-07-09)
------------------------
* Add long_description_content_type to setup.cfg

pyvcd-0.2.2 (2020-07-09)
------------------------
* Add register_alias() for creating aliases to VCD variables (#15).

pyvcd-0.2.1 (2020-04-05)
------------------------
* Add python_requires >=3.6 to setup
* Packaging changes related to PEP-517

pyvcd-0.2.0 (2020-04-01)
------------------------
* Breaking changes:

  * Python 3.6 is minimum version; drop Python 2 support
  * Remove ident argument from VCDWriter.register_var()

* Deprecations:

  * Enums for scope, variable, and timescale types
  * Enums for GTKWave flags and colors

* Features:

  * Inline type annotations, checkable with Mypy
  * Use base-94 encoding for variable identifiers
  * Improved performance

* Repairs:

  * Repair default string variable value
  * Ensure compound vector value correctness

* Development environment changes:

  * Add top-level Makefile with targets for common commands
  * Format code using black
  * Format imports using isort
  * Check type annotations with Mypy
  * Use GitHub Actions for CI; drop Travis

pyvcd-0.1.7 (2020-01-24)
------------------------
* Repair event variable changes (#14)

pyvcd-0.1.6 (2019-12-26)
------------------------
* Repair mis-formatted variable identifiers in dumps
* Exclude event and string types from dump_off
* Avoid duplicate timestamps in VCD output
* Avoid duplicate values in VCD output
* Improve performance when registering many variables in a scope (#12)

pyvcd-0.1.5 (2019-12-04)
------------------------
* Improve runtime performance by using write() (#9)
* Update package classifiers to note Python 3.8 support

pyvcd-0.1.4 (2018-12-18)
------------------------
* Add "string" variable type
* Repair deprecated import of ABC's from collections.abc

pyvcd-0.1.3 (2017-02-21)
------------------------
* Allow initial timestamp other than 0 (#2)
* Repair unit tests to work on Windows (#3)

pyvcd-0.1.2 (2016-08-09)
------------------------
* GTKWSave per-group color cycles

pyvcd-0.1.1 (2016-07-06)
------------------------
* Improve README.rst
* Update copyright owner
* Use setuptools_scm to manage package version

pyvcd-0.1.0 (2016-07-05)
------------------------
* Initial public release
