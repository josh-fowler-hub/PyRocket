"""PyRocket: importable propulsion, flight and analysis tools.

Importing this package does not run a simulation, launch a shell or open plots.
"""
from . import propulsion, flight, analysis, atmosphere

__version__ = '0.2.0'


def load(path):
    """Load a validated TOML configuration."""
    from .config import Configuration
    return Configuration(path)


def run(config, name=None):
    """Run a configured calculation or full simulation; return its result envelope."""
    from .workflows import execute
    return execute(config, name)


def interactive(config=None):
    """Enter the interactive PyRocket environment."""
    from .shell import launch
    return launch(config)


def plot(result, output=None, field=None):
    """Show or save a result envelope returned by run()."""
    from .plotting import plot_result
    return plot_result(result, output, field)
