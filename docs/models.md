# Models and numerical assumptions

## Ideal nozzle

Nozzle sizing uses ideal isentropic expansion with constant gamma and molecular
weight, a sonic throat, and a supersonic exit. Given chamber and exit pressures,
chamber temperature, and mass flow, it computes Mach number, throat/exit areas,
exhaust velocity, characteristic velocity, thrust, and specific impulse.

`R_specific = 8314.46261815324 / molecular_weight`, with molecular weight in
kg/kmol. Thrust is momentum thrust plus `(exit_pressure - ambient_pressure) *
exit_area`. Specific impulse uses standard gravity 9.80665 m/s². Exit pressure
must be positive and no higher than sonic throat pressure.

There are no viscous, thermal, divergence, or separation losses, no contour
solver, and no structural/thermal design. A scalar sizing point has no plotable
time curve. The motor model evaluates nozzle behavior during a burn.

## Motor burn

The motor contains cylindrical annular grains with either inhibited or burning
ends. The burn law is

```text
rate = a * exp(sigma * (T - T_ref)) * chamber_pressure**n
```

Rate is m/s; pressure is Pa; `a` therefore has units m/s/Pa**n. Temperatures here
are propellant temperatures affecting burn sensitivity. Quasi-steady mass
balance equates generated mass flow to `Pc * At / cstar` to solve chamber
pressure. This is not a chamber filling or ignition transient model.

The driver advances web distance explicitly with the current burn rate.
Steps shorten at geometric burnout and at the time limit. Impulse uses the
same step's thrust and duration (left-rectangle integration). An optional radial
throat-erosion rate is proportional to chamber pressure. A final zero-thrust
burnout sample retains cumulative impulse.

Termination is `burnout`, `max_time`, or `max_steps`; `completed` is true only
for burnout. Invalid choked-flow conditions or a throat eroded beyond the exit
area raise errors. There is no pressure tail, combustion instability model,
flow-separation correction, or automatic calibration. Decrease the time step
and check convergence before interpreting changed inputs.

## Planar flight

The flight model adapts the ME-426 controls final project's equations. It uses
central inverse-square gravity with `G = 6.67408e-11`, a fixed spherical planet,
variable vehicle mass, pitch dynamics, and a saturated PID gimbal controller.
At launch, the vehicle lies on +x and pitch zero points radially outward.
The body thrust direction in inertial coordinates is `theta - beta`.

The retained inertia convention is `m * radius² / 4 + m * length² / 3`.
The controller uses pitch error, negative angular rate, and accumulated pitch
error. There is a configurable activation delay and gimbal limit. There is no
integral anti-windup model.

Integration uses fixed-step RK4, with shortened steps at control activation,
thrust-history boundaries, cutoff, and the requested end time. Impacts are
located by interpolation on the final step chord and terminate propagation.
Flight terminates at `impact`, `max_time`, or `max_steps`. Reaching `max_time`
is not proof of a stable orbit or completion of a mission.

Standalone constant thrust consumes mass at `thrust / (Isp * 9.81)`, retaining
the coursework's Earth reference gravity; dry mass can force an earlier cutoff.
With motor history, reference thrust is held over each interval and corrected
for local pressure at each integration stage. Remaining propellant is linearly
interpolated, and total mass adds configured dry mass. An incomplete
motor history is not accepted by coupled execution.

Earth flight defaults to U.S. Standard Atmosphere 1976 pressure. Reference motor
pressure is converted to local nozzle pressure thrust at every RK4 stage:

```text
F_local = F_reference + (P_reference - P_atmosphere(altitude)) * exit_area
```

This preserves momentum thrust and avoids subtracting ambient pressure twice.
The adjustment is applied only during powered intervals; coast thrust remains
zero. The choked-flow regime is checked against local pressure. Grain regression
and chamber mass balance remain precomputed, since the current choked model does
not couple ambient pressure into regression. The saved `motor` result is the
reference-pressure curve; flight history records actual adjusted thrust and
`ambient_pressure_pa`.

Optional empirical drag is described below. Rotation, staging, lift and
aerodynamic moments are not modeled.
Standalone constant-thrust flight specifies net thrust, without nozzle geometry;
pressure is recorded but does not modify that prescribed force. Mars examples
use explicit vacuum because US1976 is an Earth atmosphere. GUI animation from
the coursework is not included.

### U.S. Standard Atmosphere 1976 pressure

The implementation uses the seven hydrostatic lower-atmosphere layers, with
standard sea-level pressure 101325 Pa and temperature 288.15 K. Geometric
altitude is converted to geopotential height using the standard 6356766 m
geopotential Earth radius. Pressure is continuous across lapse-rate and
isothermal layers. See the [NOAA/NASA/USAF standard](https://ntrs.nasa.gov/citations/19770009539)
and [NASA layer reference](https://ntrs.nasa.gov/citations/20050207438).

Supported geometric altitudes are 0–86 km. The standard's upper-atmosphere
composition/diffusion model is not implemented: higher altitudes raise an error
rather than extrapolating a lower layer or replacing the atmosphere with vacuum.
This is a standard reference atmosphere, not local weather data.

## Data reduction and illustrative curves

Thrust data analysis integrates trapezoids over supplied time samples, uses
impulse divided by duration for average thrust, and uses 9.80665 m/s² for
specific impulse. It does not infer ignition or burnout outside that interval.
CSV lbf values convert to N before integration. Analysis permits signed thrust
samples, which can affect net impulse.

The progressive, neutral and regressive grain polynomials are illustrative
curves with unspecified force units. Their plateaus depend on the sampling,
and they retain signed values and terminal samples. They are not the motor
model's physical grain-regression law.

## Historical formula catalog

The three `legacy.v0`, `legacy.v1`, and `legacy.v2` catalogs preserve original
parameter names and version-specific formulas. Shared identical functions live
in `legacy.common`. Atmosphere and flight functions retain imperial conventions.
`p2_p0` and `T2_T0` return stagnation-to-static ratios despite their names, and
historical `Total_Impulse` resets when thrust is zero. These behaviors are not
used as substitutes for the modern SI models.

Catalog initialization replaces historical Newton Mach solvers with bounded
bisection; `x_0 < 1` selects the subsonic branch. Version 2 retains its disabled
flow return of zero. The version 0 thrust-coefficient sweep preserves its
empirical clamp while handling cases without separation. Other version-specific
formulas remain historical references; inspect signatures and units before use.

## Aerodynamic drag

`drag_model="mae540"` evaluates the archived MAE-540 Mach-dependent coefficient
with US1976 density and sound speed. Reference area defaults to the circular
frontal area from `diameter_m`, or can be supplied as `reference_area_m2`.
In stationary air, the force is opposite the inertial velocity vector:
`F_drag = -0.5 * rho * Cd * A * |v| * v`. It is applied at every RK4 stage,
during both powered flight and coast, including descent. SI density and force
remove the imperial gravitational conversion used in the archived scalar code.

The coefficient has piecewise branches at Mach 0.6, 1.2, 1.8 and 4.0; small
jumps in the original curve are retained. It is not calibrated to each example's
vehicle geometry. There is no wind, lift, angle-of-attack dependence or aerodynamic
torque. The default `drag_model="none"` permits explicit pressure-only comparisons;
Earth examples set `"mae540"`. See [archive findings](archive-findings.md) for provenance.

The atmosphere API now also returns molecular-scale temperature, ideal-gas
density `P/(R*T)`, and calorically perfect air sound speed `sqrt(1.4*R*T)`.
These use the same lower-atmosphere constants and geometric-to-geopotential
conversion as pressure. Temperature is the molecular-scale approximation at
the upper end of the supported lower-atmosphere interval.
