# Development

## Layout

```text
src/PyRocket/       Importable application package
  propulsion/      Nozzle, grain, motor simulation
  flight/          Dynamics, controller, flight simulation
  atmosphere.py    US1976 lower-atmosphere pressure
  analysis.py      Thrust reduction
  data.py          CSV adapter
  config.py        TOML loader
  calculations.py  Calculation registry
  workflows.py     Configured subsystem orchestration
  shell.py         Interactive interface
  cli.py           Batch interface and entry point
  plotting.py      Optional Matplotlib adapter
  legacy/          Version-specific historical formulas
examples/          TOML inputs and runnable workflow script
data/              Sample measurements and regression data
tests/             Unit and integration tests
docs/              User and model documentation
```

## Install and verify

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[plot]'
python -m unittest discover -s tests -v
python examples/nozzle_to_flight.py --output-dir outputs/nozzle-to-flight
```

The project uses setuptools with `src` package discovery. Python 3.10 needs
Tomli; newer Python versions use `tomllib`. NumPy is a core dependency and
Matplotlib is optional. Install before testing; do not rely on the checkout
root being importable. Generated outputs, caches, build directories, and package
metadata are not source files.

Calculations should return data without opening files or windows. Keep model
units explicit, put I/O in adapters, and keep shell behavior out of simulation
functions. Public entry points are documented in [api.md](api.md). For a new
catalog calculation, register its function, document its arguments/units, and
add tests for meaningful physical or numerical invariants and invalid inputs.

The tests check nozzle reference values, grain regression references, CSV
integration, TOML/session errors, motor conservation and convergence, flight
coast energy and mass cutoff, motor-to-flight transfer, and figure export.
The workflow test additionally checks that the sized geometry is transferred
and the generated configurations reproduce the staged results. Passing these
checks establishes software consistency, not validation against a physical
motor or flight dataset.
