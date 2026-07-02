"""
migrations -- Versioned state migrations for MCE pipeline.
===========================================================

Each migration is a numbered Python module (``001_xxx.py``, ``002_xxx.py``)
containing a ``Migration`` class with an ``up()`` method.  The
:class:`~core.intelligence.pipeline.mce.migration_runner.MigrationRunner`
discovers and executes them in order.

Version: 1.0.0
Date: 2026-04-01
Epic: MCE-V2 / Story MCE2-1.7
"""
