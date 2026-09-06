"""Versioned TOML configuration, with paths relative to the configuration file."""
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from .calculations import validate


class Configuration:
    def __init__(self, path):
        self.path = Path(path).resolve()
        with self.path.open('rb') as stream:
            data = tomllib.load(stream)
        unknown = set(data) - {'version', 'calculations', 'simulation', 'flight'}
        if unknown:
            raise ValueError(f'unknown configuration keys: {", ".join(sorted(unknown))}')
        if type(data.get('version')) is not int or data['version'] != 1:
            raise ValueError('configuration requires version = 1')
        self.calculations = data.get('calculations', {})
        if not isinstance(self.calculations, dict):
            raise ValueError('calculations must be a table of named calculations')
        for name, entry in self.calculations.items():
            if not isinstance(entry, dict) or set(entry) - {'type', 'parameters'}:
                raise ValueError(f'calculation {name}: expected type and parameters tables')
            kind = entry.get('type')
            if not isinstance(kind, str):
                raise ValueError(f'calculation {name}: type must be a string')
            parameters = entry.get('parameters', {})
            validate(kind, parameters)
            if kind == 'analyze':
                if not isinstance(parameters.get('input'), str):
                    raise ValueError(f'calculation {name}: input must be a path string')
                parameters['input'] = str((self.path.parent / parameters['input']).resolve())
        self.simulation = data.get('simulation')
        if self.simulation is not None:
            if not isinstance(self.simulation, dict):
                raise ValueError('simulation must be a table')
            validate('simulation', self.simulation)
        self.flight = data.get('flight')
        if self.flight is not None:
            validate('flight', self.flight)
            if 'motor_history' in self.flight:
                raise ValueError('motor_history is supplied by [simulation], not TOML')
        if not self.calculations and self.simulation is None and self.flight is None:
            raise ValueError('configuration must define calculations or a simulation')

    def protected_paths(self):
        return {self.path} | {Path(entry['parameters']['input']).resolve()
                            for entry in self.calculations.values() if entry['type'] == 'analyze'}

    def calculation(self, name):
        if name not in self.calculations:
            raise ValueError(f'no configured calculation named {name!r}; use list')
        entry = self.calculations[name]
        return entry['type'], entry.get('parameters', {})
