"""Orchestrate configured calculations without importing the interactive shell."""
from .calculations import calculate


def execute(config, name=None, simulation=False):
    if config is None:
        raise ValueError('load a TOML file first: load examples/motor.toml')
    if simulation or name in {'simulate', 'simulation', None} or name == 'flight' and config.flight is not None:
        if config.flight is not None:
            from .flight import simulate as flight_simulation
            motor = calculate('simulation', config.simulation)['result'] if config.simulation is not None else None
            if motor is not None and not motor['summary']['completed']:
                raise ValueError('motor simulation must reach burnout before flight integration')
            result = flight_simulation(**config.flight, **({'motor_history': motor['history']} if motor is not None else {}))
            if motor is not None:
                result['motor'] = motor
            return {'calculation': 'flight', 'result': result}
        if config.simulation is None:
            raise ValueError('configuration has no [simulation] table')
        return calculate('simulation', config.simulation)
    if name not in config.calculations:
        matches = [key for key, entry in config.calculations.items() if entry['type'] == name]
        if len(matches) > 1:
            raise ValueError(f'{name} matches multiple calculations; use run NAME: {", ".join(matches)}')
        if matches:
            name = matches[0]
    return calculate(*config.calculation(name))
