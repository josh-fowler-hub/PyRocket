# Python API

Install the package, then `import PyRocket`. Importing it does not run a
simulation, enter a shell, or import Matplotlib's GUI interface.

## Application API

| Function | Contract |
| --- | --- |
| `PyRocket.load(path)` | Return a validated `Configuration` from TOML |
| `PyRocket.run(config, name=None)` | Return a calculation envelope; omitted name runs the configured simulation |
| `PyRocket.plot(result, output=None, field=None)` | Plot an envelope; omitted output opens a GUI window |
| `PyRocket.interactive(config=None)` | Enter the shell, optionally with a loaded configuration |

```python
import PyRocket

config = PyRocket.load("examples/earth-flight.toml")
response = PyRocket.run(config)
flight = response["result"]
print(flight["summary"])
PyRocket.plot(response, "altitude.png")
PyRocket.plot({"calculation": "simulation", "result": flight["motor"]}, "thrust.png")
```

`Configuration` exposes `path`, `calculations`, `simulation`, and `flight`.
These tables are ordinary mutable dictionaries; changing them does not rewrite
the source file. Prefer copying a table before making exploratory changes.
Loading errors include `OSError` and `ValueError`; model validation errors are
reported as `ValueError`. Programmatic callers should handle these exceptions.

## Independent subsystems

Subsystem functions return their raw result, not the application envelope.
Their inputs and defaults are documented in [configuration](configuration.md)
and their docstrings.

```python
from PyRocket import propulsion, analysis, flight

sizing = propulsion.nozzle(
    chamber_pressure=1e6, exit_pressure=1e5, ambient_pressure=0,
    temperature=2400, mass_flow=0.2, molecular_weight=24, gamma=1.2)
exit_mach = propulsion.mach_from_area(5.0, 1.2)
reduction = analysis.analyze([0, 1, 2], [0, 100, 0], propellant_mass=0.1)
coast_and_ascent = flight.simulate(max_time_s=60)
```

- `propulsion.nozzle(...)`: scalar sizing/performance dictionary with SI units
  encoded in keys where applicable.
- `propulsion.mach_from_area(area_ratio, gamma, subsonic=False)`: scalar Mach
  number from bounded bisection; area ratio must be at least one.
- `propulsion.grain_curves(samples=10)`: rows of time, progressive, neutral and
  regressive illustrative values, including two terminal samples.
- `propulsion.simulate(...)`: motor `summary` and `history` dictionaries.
- `analysis.analyze(time, thrust, propellant_mass=None)`: summary from SI arrays.
- `analysis.analyze_csv(input, ...)`: summary plus selected SI samples in `history`.
- `flight.simulate(..., motor_history=None)`: flight `summary` and `history`.

For direct coupling:

```python
import PyRocket

config = PyRocket.load("examples/earth-flight.toml")
motor = PyRocket.propulsion.simulate(**config.simulation)
if not motor["summary"]["completed"]:
    raise ValueError("Motor did not reach burnout")
trajectory = PyRocket.flight.simulate(
    **config.flight, motor_history=motor["history"])
```

Motor histories must start at time zero, have finite, strictly increasing time,
nonnegative thrust and propellant mass, nonincreasing propellant mass, and end
with zero thrust and effectively zero propellant. The flight adapter adds dry
mass, interpolates propellant mass, and adjusts reference thrust for altitude-dependent pressure over motor intervals.

## Result fields

Motor summary fields include `termination`, `completed`, `duration_s`, initial
and consumed propellant mass, total impulse, and specific impulse. Motor history
contains `time_s`, `web_m`, `propellant_mass_kg`, `burn_area_m2`,
`chamber_pressure_pa`, `burn_rate_m_s`, `mass_flow_kg_s`, `throat_area_m2`,
`exit_pressure_pa`, `thrust_n`, `total_impulse_n_s`, `exit_area_m2`,
`ambient_pressure_pa`, and `throat_pressure_pa`.

Flight summary contains `termination`, `duration_s`, `burn_cutoff_s`,
`max_altitude_m`, and `final_mass_kg`. Flight history contains `time_s`, `x_m`,
`y_m`, `vx_m_s`, `vy_m_s`, `altitude_m`, `speed_m_s`, `pitch_rad`,
`pitch_rate_rad_s`, `mass_kg`, `thrust_n`, and `ambient_pressure_pa`.

The application envelope adds `calculation` and `result`, plus optional legacy
`messages`. Coupled application runs add the full motor result at
`response['result']['motor']`. Direct `flight.simulate` does not add this copy.

## Calculation catalog

`PyRocket.calculations.calculate(type_name, parameters)` invokes a catalog
function with validation and returns an envelope. `describe(type_name)` returns
its signature and documentation. Catalog execution captures historical printed
diagnostics and normalizes NumPy values to JSON-compatible values.
Versioned formulas are retained under `PyRocket.legacy`; prefer catalog execution
for its validation and bounded Mach-solver replacements. Historical units and
quirks are documented in [models](models.md).

## Standard atmosphere

`PyRocket.atmosphere.pressure(altitude_m)` returns U.S. Standard Atmosphere 1976
pressure in Pa for geometric altitude in metres above mean sea level, from 0 to
86000 m. Invalid or unsupported altitudes raise `ValueError`. The geometric to
geopotential conversion is handled internally. Flight clamps below-surface RK4
trial positions to sea-level pressure while locating impact.

`flight.simulate` now defaults to Earth mass/radius and `atmosphere="us1976"`.
For a vacuum or Mars calculation, select `atmosphere="vacuum"` explicitly and
supply the desired planet parameters. Motor histories supplied for atmospheric
flight require nozzle exit area, reference ambient pressure, and sonic throat
pressure in every row. Burn rate and mass history remain quasi-steady inputs;
flight adjusts nozzle pressure thrust at each RK4 stage and rejects loss of the
choked-flow regime.

## Atmosphere properties and drag

`PyRocket.atmosphere.properties(altitude_m)` returns `pressure_pa`,
`temperature_k`, `density_kg_m3`, and `speed_of_sound_m_s` for the same 0–86 km
geometric interval as `pressure`. `PyRocket.flight.drag(vx_m_s, vy_m_s,
density_kg_m3, speed_of_sound_m_s, reference_area_m2)` returns SI drag components,
magnitude, Mach, coefficient, and dynamic pressure.

Flight accepts `drag_model="none"` or `"mae540"` and optional
`reference_area_m2`. The latter defaults to pi × diameter² / 4. Each flight
history row includes `drag_n`, `drag_x_n`, and `drag_y_n`; with drag enabled it
also includes `mach_number`, `drag_coefficient`, and `dynamic_pressure_pa`.
These fields can be selected for plotting. No-drag runs omit Mach/coefficient
and dynamic-pressure diagnostics rather than inventing vacuum Mach values.
