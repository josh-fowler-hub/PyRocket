"""Plot calculation results using an optional Matplotlib installation."""

LABELS = {
    'drag_n': 'Drag magnitude (N)', 'drag_x_n': 'Drag x component (N)',
    'drag_y_n': 'Drag y component (N)', 'mach_number': 'Mach number',
    'drag_coefficient': 'Drag coefficient', 'dynamic_pressure_pa': 'Dynamic pressure (Pa)',
    'ambient_pressure_pa': 'Ambient pressure (Pa)',
    'altitude_m': 'Altitude (m)', 'speed_m_s': 'Speed (m/s)',
    'pitch_rad': 'Pitch (rad)', 'pitch_rate_rad_s': 'Pitch rate (rad/s)',
    'mass_kg': 'Vehicle mass (kg)', 'x_m': 'Inertial x (m)', 'y_m': 'Inertial y (m)',
    'vx_m_s': 'Inertial x velocity (m/s)', 'vy_m_s': 'Inertial y velocity (m/s)',
    'time_s': 'Time (s)', 'thrust_n': 'Thrust (N)',
    'chamber_pressure_pa': 'Chamber pressure (Pa)', 'exit_pressure_pa': 'Exit pressure (Pa)',
    'propellant_mass_kg': 'Remaining propellant (kg)', 'burn_rate_m_s': 'Burn rate (m/s)',
    'mass_flow_kg_s': 'Mass flow (kg/s)', 'web_m': 'Regression (m)',
    'burn_area_m2': 'Burn area (m²)', 'throat_area_m2': 'Throat area (m²)',
    'total_impulse_n_s': 'Total impulse (N·s)',
}


def series_for(response, field=None):
    if response is None:
        raise ValueError('run a calculation or simulation first')
    result = response['result']
    if isinstance(result, dict) and 'history' in result:
        rows = result['history']
        field = field or ('altitude_m' if response['calculation'] == 'flight' else 'thrust_n')
        if field == 'trajectory' and response['calculation'] == 'flight':
            return [r['x_m'] for r in rows], {'trajectory': [r['y_m'] for r in rows]}, 'Inertial x (m)', 'Inertial y (m)'
        if not rows or field not in rows[0] or field == 'time_s':
            choices = ', '.join(key for key in rows[0] if key != 'time_s') if rows else '(none)'
            raise ValueError(f'choose a history field: {choices}')
        return [row['time_s'] for row in rows], {field: [row[field] for row in rows]}, 'Time (s)', LABELS.get(field, field)
    if response['calculation'] == 'grain':
        names = ['progressive', 'neutral', 'regressive']
        if field and field not in names:
            raise ValueError('grain field must be progressive, neutral, or regressive')
        return ([row[0] for row in result],
                {name: [row[i + 1] for row in result] for i, name in enumerate(names) if not field or field == name},
                'Time (s)', 'Illustrative curve value')
    if isinstance(result, list) and result and all(isinstance(v, (int, float)) for v in result):
        if field:
            raise ValueError('array results do not have named fields')
        return list(range(len(result))), {response['calculation']: result}, 'Sample index', 'Calculation value (original units)'
    raise ValueError('this result has no curve to plot; run a simulation, analyze, grain, or array calculation')


def plot_result(response, output=None, field=None):
    x, series, xlabel, ylabel = series_for(response, field)
    try:
        if output:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            figure = Figure(figsize=(9, 5), tight_layout=True)
            FigureCanvasAgg(figure)
        else:
            import matplotlib.pyplot as plt
            if 'agg' == plt.get_backend().lower() or plt.get_backend().lower() in {'pdf', 'svg', 'ps', 'template', 'cairo'}:
                raise ValueError('no interactive plotting backend; save with plot OUTPUT.png instead')
            figure = plt.figure(figsize=(9, 5), tight_layout=True)
    except ImportError as exc:
        raise ValueError('plotting requires: pip install "rocket-internal-ballistics[plot]"') from exc
    try:
        axis = figure.subplots()
        for name, values in series.items():
            axis.plot(x, values, label=LABELS.get(name, name))
        axis.set(xlabel=xlabel, ylabel=ylabel, title=response['calculation'])
        if field == 'trajectory':
            axis.set_aspect('equal', adjustable='datalim')
        axis.grid(True, alpha=0.3)
        axis.legend()
        if output:
            figure.savefig(output)
        else:
            plt.show()
    finally:
        if not output:
            plt.close(figure)
