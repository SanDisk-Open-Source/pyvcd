PyVCD
=====

The PyVCD package writes and reads Value Change Dump (VCD) files as
specified in clause 21.7 of IEEE 1800-2023, which supersedes IEEE
1364-2005 without changing the VCD format.

Read the `documentation <http://pyvcd.readthedocs.io/en/latest/>`_.

Visit `PyVCD on GitHub <https://github.com/SanDisk-Open-Source/pyvcd>`_.

.. image:: https://readthedocs.org/projects/pyvcd/badge/?version=latest
   :target: http://pyvcd.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/SanDisk-Open-Source/pyvcd/workflows/CI/badge.svg
   :target: https://github.com/SanDisk-Open-Source/pyvcd/actions?query=workflow%3ACI

.. image:: https://coveralls.io/repos/github/SanDisk-Open-Source/pyvcd/badge.svg?branch=master
   :target: https://coveralls.io/github/SanDisk-Open-Source/pyvcd?branch=master

Quick Start
-----------

.. code::

   >>> import sys
   >>> from vcd import VCDWriter
   >>> with VCDWriter(sys.stdout, timescale='1 ns', date='today') as writer:
   ...     counter_var = writer.register_var('a.b.c', 'counter', 'integer', size=8)
   ...     real_var = writer.register_var('a.b.c', 'x', 'real', init=1.23)
   ...     for timestamp, value in enumerate(range(10, 20, 2)):
   ...         writer.change(counter_var, timestamp, value)
   ...     writer.change(real_var, 5, 3.21)
   $date today $end
   $timescale 1 ns $end
   $scope module a $end
   $scope module b $end
   $scope module c $end
   $var integer 8 ! counter $end
   $var real 64 " x $end
   $upscope $end
   $upscope $end
   $upscope $end
   $enddefinitions $end
   #0
   $dumpvars
   b1010 !
   r1.23 "
   $end
   #1
   b1100 !
   #2
   b1110 !
   #3
   b10000 !
   #4
   b10010 !
   #5
   r3.21 "

PyVCD and the waveform ecosystem
--------------------------------

PyVCD is a pure-Python library for *producing* VCD files and their GTKWave
companions, and for *tokenizing* VCD files exactly as written:

* ``vcd.writer`` streams standard VCD from Python programs.
* ``vcd.reader`` yields every declaration and value change as a typed token
  with exact file locations, suiting linters, filters, and translators. It
  tolerates the nonstandard output of real-world simulators.
* ``vcd.gtkw`` generates GTKWave save files: trace layout, groups, combined
  vectors, colors, and filters.

PyVCD is deliberately not a bulk waveform reader. To load signal values
from large VCD, FST, or GHW files, use `pywellen`_, the Python bindings of
the Rust wellen library that powers the Surfer viewer. To produce FST,
write VCD with PyVCD and convert with GTKWave's ``vcd2fst``, or have your
simulator emit FST directly.

.. _pywellen: https://pypi.org/project/pywellen/
