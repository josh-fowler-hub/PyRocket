# Rocket Internal Ballistics

Standalone rocket internal-ballistics and nozzle-performance simulation tool,
grown out of MAE-540 (Rocket Propulsion) coursework. Not tied to any specific
piece of hardware - covers general solid/hybrid motor performance analysis:

- Solid rocket motor (SRM) thrust-curve reduction and specific-impulse
  calculation from static-fire data (`MAE-540_HW2_SRM-1_prob.py`)
- Progressive/neutral/regressive fuel grain burn-back thrust modeling
  (`fuel_grain_Thrust.py`)
- De Laval nozzle theory and combustion/expansion performance
  (`Combustion_Nozzle.py`, `nozzle_design.py`)
- Nozzle area-ratio / Mach-number solvers and method-of-characteristics
  contour generation, iterated across versions (`Nozzle_Funcs.py`,
  `Nozzle_Funcs_1.py`, `Nozzle_Funcs_2.py`)

See also: [HybridRocketTestStand](../HybridRocketTestStand) - a separate
senior capstone project for the physical test stand hardware.

## Contents

- `python/` - simulation scripts listed above
- `misc/` - sample data (SRM-1 static-fire dataset, fuel grain thrust CSV),
  generated plots, and nozzle contour output
- `docs/` - reference material (nozzle performance)
