# Nozzle sizing through flight

Run all commands from the repository root after installing `.[plot]`.
This tutorial uses [nozzle-to-flight.toml](../examples/nozzle-to-flight.toml)
and [nozzle_to_flight.py](../examples/nozzle_to_flight.py). The Python script
connects the existing public APIs; no extra command or TOML reference syntax is
required.

## 1. Specify and evaluate a nozzle design point

The input includes `[calculations.nozzle_design]` with `type = "nozzle"`.
Its parameters specify 1 MPa chamber pressure, 0.1 MPa exit pressure, 2400 K
chamber temperature, 0.2 kg/s mass flow, molecular weight 24 kg/kmol, and gamma
1.2. Reference ambient pressure is 101325 Pa (standard sea level). Exit
pressure remains positive: zero exit pressure would require an unbounded ideal
expansion.

You can inspect that sizing result alone:

```bash
pyrocket run examples/nozzle-to-flight.toml nozzle_design
```

The output reports throat area, exit area, area ratio, exit Mach, exhaust
velocity, thrust, and characteristic velocity. This is ideal flow-area sizing,
not structural design, contour generation, or a time-dependent nozzle run.

## 2. Transfer the nozzle into a motor and simulate it

```bash
python examples/nozzle_to_flight.py --output-dir outputs/nozzle-to-flight
```

The workflow copies the `[simulation]` parameters and replaces these fields:

| Motor field | Source |
| --- | --- |
| `throat_radius_m` | `sqrt(throat_area_m2 / pi)` from sizing |
| `exit_area_m2` | Sizing exit area |
| `characteristic_velocity_m_s` | Sizing characteristic velocity |
| `gamma` | Nozzle input gamma |
| `ambient_pressure_pa` | Nozzle input ambient pressure |

The source TOML is not modified. Its geometry values serve as valid starting
values; the workflow overwrites them in memory and writes the final parameters
to `motor.toml`. **Running the source TOML directly with `simulate` does not
perform this sizing transfer.** Use the script or its generated configurations
for the connected workflow.

The motor simulation evaluates grain regression, chamber pressure and nozzle
performance at each time step. There is no separate transient nozzle solver:
the nozzle is evaluated within the quasi-steady motor model. The chamber
pressure and mass flow are determined by the grain, burn law, and throat; the
sizing point is not imposed throughout the burn. Temperature in `[simulation]`
is propellant temperature for burn-rate sensitivity, not the nozzle's chamber
gas temperature.

## 3. Use the generated thrust curve in flight

The script passes the motor history directly to `PyRocket.flight.simulate`.
Reference thrust is held over each motor interval; the nozzle pressure term
is adjusted using US1976 pressure at every flight integration stage. Remaining propellant mass is
interpolated and added to the configured 5 kg dry vehicle mass. The motor must
reach burnout before flight starts. The flight model integrates the powered
phase and then coasts to impact or the configured run limit.

This is a vertical Earth demonstration with US1976 ambient pressure and zero
pitch measured from the outward radial direction at launch. Gravity uses Earth's
configured mass and mean radius. The MAE-540 empirical drag curve is enabled, using atmospheric density and
sound speed. Planetary rotation remains absent. Pressure is supported from 0 to 86 km; higher altitudes raise an error.

## Outputs and rerunning stages

| Output | Contents |
| --- | --- |
| `nozzle.json` | Nozzle sizing result envelope |
| `motor.json` | Motor summary and time history |
| `flight.json` | Flight summary/history, with the motor result at `result.motor` |
| `motor.toml` | Transferred nozzle parameters plus motor settings |
| `flight.toml` | The same motor settings plus flight settings |
| `thrust.png`, `pressure.png` | Motor histories |
| `altitude.png`, `trajectory.png` | Flight histories |

Existing output files are replaced. Use `--no-plots` without the plotting extra.
`--config PATH` selects an edited workflow input. Output directories are created
by the example script; ordinary CLI output paths require an existing parent.

```bash
pyrocket simulate outputs/nozzle-to-flight/motor.toml --output outputs/nozzle-to-flight/motor-rerun.json
pyrocket simulate outputs/nozzle-to-flight/flight.toml --output outputs/nozzle-to-flight/flight-rerun.json
```

The flight configuration reruns the motor and then feeds the newly computed
history to flight; it does not load the saved `motor.json`. The example script
itself passes the already-computed history directly between Python functions.

You can inspect the generated stages interactively:

```text
$ pyrocket
pyrocket> load outputs/nozzle-to-flight/motor.toml
pyrocket> simulate
pyrocket> plot thrust.png
pyrocket> plot pressure.png chamber_pressure_pa
pyrocket> load outputs/nozzle-to-flight/flight.toml
pyrocket> simulate
pyrocket> plot altitude.png
pyrocket> plot trajectory.png trajectory
pyrocket> exit
```

The motor must report `burnout` and flight should report `impact` for these
inputs. Values change with nozzle sizing, reference ambient pressure, and the
flight atmosphere. These are demonstration outputs, not validated physical
predictions. Reduce time steps to assess convergence when changing inputs.
