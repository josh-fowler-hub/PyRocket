# Reviewed archive material

The following local directories were inspected read-only:

- `~/Documents/Old_Stuff_From_HardDrive/passport/DVR_Research`
- `~/Documents/Old_Stuff_From_HardDrive/passport/MAE-540`

## Atmosphere

`DVR_Research/Atmosphere.m`, credited in its header to Richard Rieber (updated
March 17, 2006), computes temperature, pressure, density and sound speed using
seven lapse-rate/isothermal layers. It includes optional imperial conversions.

The file uses rounded constants (`g=9.81`, `R=287`, `T0=288.16`) and applies
layer heights directly without geometric-to-geopotential conversion. Above its
last layer it warns without reliably assigning a new result. PyRocket retains
its existing standard constants, altitude conversion, and explicit domain errors.
The public atmosphere API has been extended to density and sound speed using
the same equations as this treatment; it does not copy those limitations.

## Drag

`MAE-540/Project/PR13/Nozzle_Funcs.py` contains `C_D(Mach)`, `Drag_Force`,
`Air_Density`, and `Speed_of_Sound_Air`. The project driver calls `Drag_Force`
and records/plots drag. The coefficient is the same historical function already
consolidated in `PyRocket.legacy.common.C_D`, so no duplicate coefficient
implementation was added.

The old scalar force uses an imperial density polynomial and division by `g0`.
The active flight adapter uses current SI atmospheric density and sound speed
and turns the drag magnitude into a vector opposing motion. The empirical Cd
curve and its branch boundaries are retained. This is a recovered coursework
model, not a validated aerodynamic database for a specific vehicle.

## Other candidate functionality

- `DVR_Research/shock.m`: normal/oblique shock property ratios. The function
  overwrites some fields of its input structure; this needs review before reuse.
- `DVR_Research/OShock.m`: console-oriented oblique-shock calculations.
- `DVR_Research/beta.m`: analytic weak/strong oblique-shock angle solution;
  header credits Chris Plumley and cites Rudd and Lewis (1998). Angles are degrees.
- `DVR_Research/Closed_Form_STAG.m`: sphere-cone stagnation heating calculations
  using atmospheric conditions and mixed imperial units; references NACA TN 4265.
- `MAE-540/HT_Code/`: fluid-property, transport-property and heat-transfer helpers.
- `MAE-540/Project/`: additional thermochemistry and motor-project drivers.

Only the atmosphere-property extension and drag adapter were integrated in this
pass. Shock, heating, and thermochemistry files need separate unit, dependency,
domain, and validation reviews before becoming application calculations.
