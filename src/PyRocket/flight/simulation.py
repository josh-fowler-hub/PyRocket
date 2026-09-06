"""Bounded RK4 planar flight with configurable atmospheric pressure (SI units)."""
import math
import numpy as np

from .control import gimbal_angle
from .dynamics import derivatives
from ..atmosphere import pressure as standard_pressure
from ..atmosphere import properties as atmospheric_properties
from .aerodynamics import drag


def simulate(initial_mass_kg=300.0, dry_mass_kg=70.0, thrust_n=15000.0,
             specific_impulse_s=291.0, burn_time_s=43.0,
             planet_mass_kg=5.972e24, planet_radius_m=6371000.0,
             length_m=3.0, diameter_m=0.5, initial_altitude_m=0.0,
             initial_vx_m_s=0.0, initial_vy_m_s=0.0,
             initial_pitch_rad=0.0, initial_pitch_rate_rad_s=0.0,
             target_pitch_rad=math.pi/2, kp=0.055, kd=0.11, ki=0.000011,
             gimbal_limit_rad=math.pi/4, control_delay_s=0.1,
             time_step_s=0.1, max_time_s=7000.0, max_steps=100000,
             motor_history=None, atmosphere='us1976', drag_model='none', reference_area_m2=None):
    """Simulate planar flight with US1976 Earth pressure or explicit vacuum.

    With motor_history, total mass is dry mass plus interpolated propellant mass;
    constant-thrust/initial-mass inputs are superseded. Motor thrust is held over
    each motor interval as a reference, with local ambient-pressure correction
    at every RK4 stage. Constant-thrust flight prescribes net force.
    """
    for name, value in locals().copy().items():
        if name in {'motor_history', 'max_steps', 'atmosphere', 'drag_model', 'reference_area_m2'}:
            continue
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
            raise ValueError(f'{name} must be a finite number')
    for name, value in [('dry_mass_kg', dry_mass_kg), ('initial_mass_kg', initial_mass_kg),
                        ('specific_impulse_s', specific_impulse_s), ('planet_mass_kg', planet_mass_kg),
                        ('planet_radius_m', planet_radius_m), ('length_m', length_m),
                        ('diameter_m', diameter_m), ('time_step_s', time_step_s), ('max_time_s', max_time_s)]:
        if value <= 0:
            raise ValueError(f'{name} must be positive')
    if min(thrust_n, burn_time_s, initial_altitude_m, control_delay_s, kp, kd, ki) < 0:
        raise ValueError('thrust, burn duration, altitude, delay and PID gains must be nonnegative')
    if not 0 <= gimbal_limit_rad <= math.pi/2:
        raise ValueError('gimbal_limit_rad must lie in [0, pi/2]')
    if type(max_steps) is not int or not 1 <= max_steps <= 1000000:
        raise ValueError('max_steps must be an integer in [1, 1000000]')
    if not isinstance(atmosphere, str) or atmosphere not in {'us1976', 'vacuum'}:
        raise ValueError('atmosphere must be us1976 or vacuum')
    if atmosphere == 'us1976' and not (6.3e6 < planet_radius_m < 6.5e6 and 5.8e24 < planet_mass_kg < 6.1e24):
        raise ValueError('us1976 is an Earth atmosphere; select vacuum explicitly for other planets')
    if not isinstance(drag_model, str) or drag_model not in {'none', 'mae540'}:
        raise ValueError('drag_model must be none or mae540')
    if drag_model != 'none' and atmosphere == 'vacuum':
        raise ValueError('mae540 drag requires an atmosphere; use drag_model=none for vacuum')
    if reference_area_m2 is None:
        reference_area_m2 = math.pi * diameter_m**2 / 4
    if isinstance(reference_area_m2, bool) or not isinstance(reference_area_m2, (int, float)) or not math.isfinite(reference_area_m2) or reference_area_m2 <= 0:
        raise ValueError('reference_area_m2 must be positive and finite')
    if motor_history is not None:
        try:
            times = np.array([r['time_s'] for r in motor_history], dtype=float)
            thrusts = np.array([r['thrust_n'] for r in motor_history], dtype=float)
            masses = np.array([r['propellant_mass_kg'] for r in motor_history], dtype=float)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('motor history requires time_s, thrust_n and propellant_mass_kg') from exc
        if (len(times) < 2 or times[0] != 0 or not np.all(np.isfinite([times, thrusts, masses]))
                or np.any(np.diff(times) <= 0) or np.any(thrusts < 0) or np.any(masses < 0)
                or np.any(np.diff(masses) > 0) or masses[-1] > 1e-9 or thrusts[-1] != 0):
            raise ValueError('motor history must be finite, monotonic, nonnegative and end at burnout')
        cutoff = float(times[-1])
        nozzle_metadata = all(all(key in row for key in ['exit_area_m2', 'ambient_pressure_pa', 'throat_pressure_pa']) for row in motor_history)
        if atmosphere == 'us1976' and not nozzle_metadata:
            raise ValueError('atmospheric motor flight requires exit_area_m2, ambient_pressure_pa and throat_pressure_pa in every motor row')
        if nozzle_metadata:
            for row in motor_history:
                if any(not math.isfinite(row[key]) or row[key] < 0 for key in ['exit_area_m2', 'ambient_pressure_pa', 'throat_pressure_pa']) or row['exit_area_m2'] == 0:
                    raise ValueError('invalid nozzle pressure metadata in motor history')
        def engine(t):
            index = min(int(np.searchsorted(times, t, side='right')) - 1, len(times)-1)
            return float(thrusts[max(0,index)]) if t < cutoff else 0.0, dry_mass_kg + float(np.interp(t, times, masses))
        boundaries = list(times[1:])
    else:
        if initial_mass_kg < dry_mass_kg:
            raise ValueError('initial mass must be at least dry mass')
        flow = thrust_n / (specific_impulse_s * 9.81)  # Coursework Earth reference gravity
        cutoff = min(burn_time_s, (initial_mass_kg-dry_mass_kg)/flow) if flow else 0.0
        def engine(t):
            return thrust_n if t < cutoff else 0.0, max(dry_mass_kg, initial_mass_kg - flow*min(t, cutoff))
        boundaries = [cutoff] if cutoff else []
    boundaries = sorted(set([*boundaries, control_delay_s, max_time_s]))
    mu = 6.67408e-11 * planet_mass_kg
    state = np.array([planet_radius_m+initial_altitude_m, initial_vx_m_s,
                      0.0, initial_vy_m_s, initial_pitch_rad, initial_pitch_rate_rad_s, 0.0])
    time = 0.0
    rows = []
    reason = 'max_steps'
    boundary_index = 0

    def ambient(z):
        return standard_pressure(max(0.0, math.hypot(z[0], z[2])-planet_radius_m)) if atmosphere == 'us1976' else 0.0

    def aerodynamic_force(z):
        if drag_model == 'none':
            return dict(drag_x_n=0.0, drag_y_n=0.0, drag_n=0.0)
        air = atmospheric_properties(max(0.0, math.hypot(z[0], z[2])-planet_radius_m))
        return drag(float(z[1]), float(z[3]), air['density_kg_m3'], air['speed_of_sound_m_s'], reference_area_m2)

    def effective_thrust(base_thrust, z, sample_time):
        pressure = ambient(z)
        if motor_history is None or sample_time >= cutoff:
            return base_thrust
        if not nozzle_metadata:
            return base_thrust  # Historical vacuum-only arrays lack nozzle geometry.
        index = max(0, min(int(np.searchsorted(times, sample_time, side='right'))-1, len(times)-1))
        source = motor_history[index]
        if source['throat_pressure_pa'] <= pressure:
            raise ValueError('flight ambient pressure exceeds the motor choked-flow regime')
        return base_thrust + (source['ambient_pressure_pa']-pressure)*source['exit_area_m2']

    def rhs(t, z, held_thrust, controlled):
        _, mass = engine(t)
        beta = gimbal_angle(z[4], z[5], z[6], target_pitch_rad, kp, kd, ki, gimbal_limit_rad) if controlled else 0.0
        derivative = derivatives(z, mass, effective_thrust(held_thrust, z, time), beta, mu, length_m, diameter_m, target_pitch_rad)
        aero = aerodynamic_force(z)
        derivative[1] += aero['drag_x_n'] / mass
        derivative[3] += aero['drag_y_n'] / mass
        return derivative

    for step in range(max_steps+1):
        force, mass = engine(time)
        base_force = force
        force = effective_thrust(base_force, state, time)
        row = dict(time_s=time, ambient_pressure_pa=ambient(state), x_m=float(state[0]), y_m=float(state[2]),
                   vx_m_s=float(state[1]), vy_m_s=float(state[3]),
                   altitude_m=max(0.0, math.hypot(state[0],state[2])-planet_radius_m),
                   speed_m_s=math.hypot(state[1],state[3]), pitch_rad=float(state[4]),
                   pitch_rate_rad_s=float(state[5]), mass_kg=mass, thrust_n=force)
        row.update(aerodynamic_force(state))
        if not all(math.isfinite(v) for v in row.values()):
            raise ValueError('flight produced a non-finite state; reduce time_step_s')
        rows.append(row)
        if step and math.hypot(state[0],state[2]) <= planet_radius_m:
            reason = 'impact'
            break
        if time >= max_time_s:
            reason = 'max_time'
            break
        if step == max_steps:
            break
        while boundary_index < len(boundaries) and boundaries[boundary_index] <= time:
            boundary_index += 1
        dt = min(time_step_s, max_time_s-time, boundaries[boundary_index]-time)
        if time+dt <= time:
            raise ValueError('time step cannot advance flight')
        controlled = time >= control_delay_s
        k1 = rhs(time, state, base_force, controlled)
        k2 = rhs(time+dt/2, state+dt*k1/2, base_force, controlled)
        k3 = rhs(time+dt/2, state+dt*k2/2, base_force, controlled)
        k4 = rhs(time+dt, state+dt*k3, base_force, controlled)
        next_state = state + dt*(k1+2*k2+2*k3+k4)/6
        # Locate a surface crossing on the step chord; never propagate underground.
        if math.hypot(next_state[0],next_state[2]) < planet_radius_m:
            low, high = 0.0, 1.0
            for _ in range(50):
                middle = (low+high)/2
                point = state + middle*(next_state-state)
                if math.hypot(point[0],point[2]) > planet_radius_m:
                    low = middle
                else:
                    high = middle
            fraction = high
            state = state + fraction*(next_state-state)
            state[[0,2]] *= planet_radius_m / math.hypot(state[0],state[2])
            time += fraction*dt
            # Ensure termination even if roundoff leaves radius just above surface.
            force, mass = engine(time)
            force = effective_thrust(force, state, time)
            rows.append(dict(time_s=time, ambient_pressure_pa=ambient(state), x_m=float(state[0]), y_m=float(state[2]),
                             vx_m_s=float(state[1]), vy_m_s=float(state[3]), altitude_m=0.0,
                             speed_m_s=math.hypot(state[1],state[3]), pitch_rad=float(state[4]),
                             pitch_rate_rad_s=float(state[5]), mass_kg=mass, thrust_n=force))
            rows[-1].update(aerodynamic_force(state))
            reason = 'impact'
            break
        state = next_state
        time += dt
    return dict(summary=dict(termination=reason, duration_s=time, burn_cutoff_s=cutoff,
                             max_altitude_m=max(r['altitude_m'] for r in rows),
                             final_mass_kg=rows[-1]['mass_kg']), history=rows)
