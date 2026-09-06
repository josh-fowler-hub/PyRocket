# PyRocket

PyRocket is a Python library and interactive application for ideal nozzle
sizing, solid-motor burn simulation, thrust-data analysis, and planar flight.
Configure calculations with TOML, run them from a terminal or Python, and export
JSON results and plots.

## Install

Requires Python 3.10 or newer. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[plot]'
pyrocket --help
```

Use `pip install -e .` if you do not need plotting. Install before running
examples or tests: application code uses the `src/PyRocket/` package layout.
`python -m PyRocket` is equivalent to the `pyrocket` command.

## Complete workflow: nozzle → motor → flight

Run the supplied [workflow script](examples/nozzle_to_flight.py) with its
[TOML input](examples/nozzle-to-flight.toml):

```bash
python examples/nozzle_to_flight.py --output-dir outputs/nozzle-to-flight
```

The example performs three connected steps:

1. **Design the nozzle:** calculate ideal throat and exit areas at a specified
   pressure, temperature, and mass-flow design point.
2. **Simulate the motor and nozzle:** transfer the designed geometry and
   characteristic velocity to the motor model, then compute chamber pressure,
   nozzle thrust, and remaining propellant through burnout.
3. **Simulate Earth flight:** feed that exact thrust and mass history into the
   flight model, then coast to surface impact.

Results include `nozzle.json`, `motor.json`, `flight.json`, and plots of thrust,
pressure, altitude, and trajectory. The generated `motor.toml` and `flight.toml`
contain the transferred nozzle parameters and can be run independently:

```bash
pyrocket simulate outputs/nozzle-to-flight/motor.toml --plot outputs/nozzle-to-flight/motor-check.png
pyrocket simulate outputs/nozzle-to-flight/flight.toml --plot outputs/nozzle-to-flight/flight-check.png
```

This example sizes ideal flow areas; it does not generate a nozzle wall contour.
The motor's pressure and mass flow evolve during the burn and need not match the
nozzle sizing point. Earth flight uses U.S. Standard Atmosphere 1976 pressure
through 86 km to adjust nozzle thrust as altitude changes. Earth examples also enable the MAE-540 empirical Mach-dependent drag model;
Mars examples select vacuum explicitly. See the [workflow guide](docs/workflow.md) for parameter handoffs,
outputs, and expected results, and [model assumptions](docs/models.md) for limits.

## Interactive use

```text
$ pyrocket
pyrocket> load examples/earth-flight.toml
pyrocket> list
pyrocket> simulate
pyrocket> plot altitude.png
pyrocket> plot speed.png speed_m_s
pyrocket> save earth-flight.json
pyrocket> exit
```

`help` lists commands; `catalog` lists calculation types. `run NAME` selects a
configured calculation. `simulate` runs the motor, flight, or connected model
according to the loaded file. `plot` without a filename opens a window when a
GUI backend is available.

For batch use:

```bash
pyrocket run examples/motor.toml nozzle_example --output nozzle.json
pyrocket simulate examples/earth-flight.toml --output earth-flight.json --plot altitude.png
pyrocket analyze data/SRM-1.csv --thrust-unit lbf --limit 265
```

## Python use

```python
import PyRocket

config = PyRocket.load("examples/earth-flight.toml")
result = PyRocket.run(config)
print(result["result"]["summary"])
PyRocket.plot(result, "altitude.png")
```

The `propulsion`, `flight`, and `analysis` modules can also be used directly.
Imports do not run simulations, start a prompt, or open plots.

## Documentation

- [Documentation index](docs/README.md)
- [Complete workflow](docs/workflow.md)
- [Commands and plotting](docs/commands.md)
- [TOML configuration and units](docs/configuration.md)
- [Python API](docs/api.md)
- [Numerical models and assumptions](docs/models.md)
- [Development and repository layout](docs/development.md)

For a demonstrated Earth ascent, use the complete workflow above. The separate
`earth-flight.toml` seed motor starts below vehicle weight at sea-level pressure
and does not lift off in the current free-flight model.

The [examples directory](examples/) includes standalone motor calculations,
Mars flight, and motor-driven Earth and Mars flight. Inputs are demonstrations,
not calibrated motor datasets.

Run tests after installation:

```bash
python -m unittest discover -s tests -v
```
