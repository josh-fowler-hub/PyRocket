# TOML configuration

Every file requires `version = 1`. The only top-level keys are `version`,
`calculations`, `simulation`, and `flight`. At least one calculation or simulation
section is required. Unknown keys, unknown calculation types, and unmatched
function arguments are rejected. Physical domain validation also occurs when a
calculation runs. Load validation is not a guarantee that every numeric value
is physically meaningful.

## Named calculations

```toml
version = 1

[calculations.exit_mach]
type = "mach"
[calculations.exit_mach.parameters]
area_ratio = 5.0
gamma = 1.2
```

Each named calculation accepts only `type` and `parameters`. Parameters are
passed by name to the calculation function; omitted optional arguments use its
defaults. Values may be numbers, strings, booleans, or arrays. No expressions,
imports, variable substitution, or cross-table references are evaluated.
Use `pyrocket catalog TYPE` to inspect the exact current signature.

| Type | Parameters and units |
| --- | --- |
| `nozzle` | Required: `chamber_pressure`, `exit_pressure`, `ambient_pressure` (Pa), `temperature` (K), `mass_flow` (kg/s), `molecular_weight` (kg/kmol), `gamma` |
| `mach` | Required: `area_ratio`, `gamma`; optional `subsonic = false` |
| `grain` | Optional `samples = 10` |
| `analyze` | Required `input` (CSV path); optional `time_column = "Time"`, `thrust_column = "Thrust"`, `thrust_unit = "N"` or `"lbf"`, `propellant_mass` (kg), `limit` (rows) |
| `simulation` | Motor parameters listed below |
| `flight` | Flight parameters listed below; an independent named calculation |
| `legacy.v0.NAME`, `legacy.v1.NAME`, `legacy.v2.NAME` | Version-specific original signatures and units; inspect with `catalog` |

Unlike the flag-based `pyrocket nozzle` command, a TOML `nozzle` calculation
requires every listed input. CSV times are seconds and strictly increasing;
only selected columns must be numeric. Optional `limit` must be at least two.
Analysis uses all rows when omitted and reports SI force and impulse. Specific
impulse requires consumed propellant mass in kg; lbm is not accepted as a unit.

## Full simulation selection

| Tables present | `simulate`, file-only `run`, or `PyRocket.run(config)` |
| --- | --- |
| `[simulation]` only | Motor burn |
| `[flight]` only | Constant-thrust flight followed by coast |
| Both | Motor burn, then flight consuming the generated history |
| Named calculations only | Error: select a name with `run FILE NAME` |

Named calculations are independent. They are not run automatically before
`simulate`, and nozzle geometry is not automatically copied between tables.
The [workflow example](workflow.md) implements that transfer explicitly.

## Motor parameters: `[simulation]`

| Parameter | Unit | Default / requirement |
| --- | --- | --- |
| `outer_radius_m`, `inner_radius_m`, `length_m` | m | Required; positive; outer > inner |
| `density_kg_m3` | kg/m³ | Required; positive |
| `burn_coefficient` | m/s/Pa**n | Required; positive |
| `burn_exponent` | Dimensionless | Required; 0 ≤ n < 1 |
| `characteristic_velocity_m_s` | m/s | Required; positive |
| `throat_radius_m` | m | Required; positive |
| `exit_area_m2` | m² | Required; ≥ throat area |
| `gamma` | Dimensionless | Required; > 1 |
| `grain_count` | Count | 1; positive integer |
| `ends_inhibited` | Boolean | true |
| `ambient_pressure_pa` | Pa | 101325; nonnegative |
| `temperature_k`, `reference_temperature_k` | K | 293.15 each; positive propellant temperatures |
| `temperature_sensitivity_per_k` | 1/K | 0 |
| `erosion_m_s_pa` | m/s/Pa | 0; nonnegative radial erosion coefficient |
| `time_step_s` | s | 0.01; positive |
| `max_time_s` | s | 120; positive |
| `max_steps` | Steps | 100000; integer from 1 to 1000000 |

## Flight parameters: `[flight]`

All numerical inputs must be finite. Angles are radians, measured from inertial
+x; at launch, +x points radially away from the planet. Setting pitch to zero
holds a vertical launch direction, rather than a horizontal direction.

| Parameter | Unit | Default |
| --- | --- | --- |
| `drag_model` | Model name | `"none"`; use `"mae540"` for the empirical Mach-dependent model |
| `reference_area_m2` | m² | Omit to use pi × diameter² / 4; otherwise positive |
| `atmosphere` | Model name | `"us1976"`; `"vacuum"` is an explicit alternative |
| `initial_mass_kg` | kg | 300 |
| `dry_mass_kg` | kg | 70 |
| `thrust_n` | N | 15000 |
| `specific_impulse_s` | s | 291 |
| `burn_time_s` | s | 43 |
| `planet_mass_kg` | kg | 5.972e24 (Earth) |
| `planet_radius_m` | m | 6371000 (Earth mean radius) |
| `length_m`, `diameter_m` | m | 3, 0.5 |
| `initial_altitude_m` | m | 0 |
| `initial_vx_m_s`, `initial_vy_m_s` | m/s | 0 each |
| `initial_pitch_rad`, `initial_pitch_rate_rad_s` | rad, rad/s | 0 each |
| `target_pitch_rad` | rad | π/2 |
| `kp`, `kd`, `ki` | PID coefficients in the radian/second convention | 0.055, 0.11, 0.000011 |
| `gimbal_limit_rad` | rad | π/4; allowed range [0, π/2] |
| `control_delay_s` | s | 0.1 |
| `time_step_s` | s | 0.1 |
| `max_time_s` | s | 7000 |
| `max_steps` | Steps | 100000; integer from 1 to 1000000 |

Masses, specific impulse, planet size/mass, geometry and time limits must be
positive. Thrust, burn time, altitude, control delay and PID gains must be
nonnegative. In standalone flight, initial mass must be at least dry mass.

With a motor table, total vehicle mass is dry mass plus generated remaining
propellant mass. Motor history supersedes `initial_mass_kg`, `thrust_n`,
`specific_impulse_s` and `burn_time_s`; omit those four fields to avoid confusion.
Do not set `motor_history` in TOML: orchestration supplies it, or Python callers
can provide it directly to `PyRocket.flight.simulate`.

## Supplied inputs

| File | Purpose |
| --- | --- |
| [motor.toml](../examples/motor.toml) | Named calculations and standalone motor burn |
| [mars-flight.toml](../examples/mars-flight.toml) | Constant-thrust Mars flight |
| [motor-flight.toml](../examples/motor-flight.toml) | Generated motor curve driving Mars flight |
| [earth-flight.toml](../examples/earth-flight.toml) | Generated motor curve driving vertical Earth flight |
| [nozzle-to-flight.toml](../examples/nozzle-to-flight.toml) | Source input for the sizing-transfer workflow script |

All examples are demonstration inputs. Output paths are command arguments, not
TOML fields. See [commands](commands.md) for path resolution and plotting.

## Atmospheric pressure

`atmosphere = "us1976"` uses standard Earth pressure from geometric altitude
0–86000 m. It is the flight default and requires Earth-like planet parameters.
Mars examples explicitly set `atmosphere = "vacuum"`; no Mars atmospheric model
is implemented. Values outside the supported Earth altitude range raise an error.

Motor `ambient_pressure_pa` is the reference pressure for the generated curve.
Flight adjusts the pressure-thrust contribution using local atmospheric pressure;
it does not hold that reference pressure throughout ascent. Motor history must
include `exit_area_m2`, `ambient_pressure_pa`, and `throat_pressure_pa` for this
correction. Current motor simulation outputs include these automatically.
Standalone constant-thrust flight prescribes net thrust and has no nozzle geometry;
its prescribed force is unchanged while ambient pressure is recorded. Use motor
coupling for pressure-dependent nozzle performance. Drag is enabled independently with `drag_model = "mae540"`. It requires
`atmosphere = "us1976"`; vacuum with enabled drag is rejected.

A named `atmosphere_pressure` calculation accepts `altitude_m` and returns Pa.

`atmosphere_properties` accepts `altitude_m` and returns temperature (K),
pressure (Pa), density (kg/m³), and speed of sound (m/s). `atmosphere_pressure`
remains available for a scalar pressure result. The drag coefficient is an
empirical coursework curve, not a geometry-specific aerodynamic prediction.
Earth examples enable it explicitly; generic API calls default to no drag.

The current `earth-flight.toml` seed motor has approximately 10 N initial
sea-level thrust versus 71 N vehicle weight. It does not lift off in the
free-flight model; the integrator reports surface impact. No launch-pad
hold-down/burn phase is modeled. For the sized nozzle with a demonstrated
ascent, use the [complete workflow](workflow.md) and its generated `flight.toml`.
The seed example is retained unchanged rather than silently resizing its motor.
