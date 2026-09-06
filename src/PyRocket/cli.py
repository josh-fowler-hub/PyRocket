"""Argument parsing and filesystem/plotting adapters."""

import argparse
import csv
import json
from pathlib import Path
import sys

from . import __version__
from .plotting import plot_result
from .analysis import analyze
from .propulsion import grain_curves, nozzle


def parser():
    root = argparse.ArgumentParser(description="PyRocket: propulsion, flight, and TOML calculations",
                                   epilog="With no command, enter the interactive shell. In the shell: load FILE, list (ls), run NAME, simulate.")
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument("--config", type=Path, help="Load a TOML file when entering the application")
    commands = root.add_subparsers(dest="command")
    commands.add_parser("shell", help="Enter the interactive application")
    run = commands.add_parser("run", help="Run a named calculation from TOML")
    run.add_argument("config", type=Path)
    run.add_argument("name", nargs="?", help="Configured name or unique type; omit to run the simulation")
    run.add_argument("--output", type=Path)
    run.add_argument("--plot", type=Path, help="Save a plot of the result")
    run.add_argument("--field", help="History or grain field to plot")
    simulation = commands.add_parser("simulate", aliases=["simulation"], help="Run a coupled motor simulation from TOML")
    simulation.add_argument("config", type=Path)
    simulation.add_argument("--output", type=Path)
    simulation.add_argument("--plot", type=Path, help="Save a simulation plot")
    simulation.add_argument("--field", help="History field to plot (default: thrust_n)")
    catalog = commands.add_parser("catalog", help="List calculation types or describe one")
    catalog.add_argument("name", nargs="?")
    n = commands.add_parser("nozzle", help="Ideal isentropic nozzle performance (SI units)")
    for name, default, help_text in [
        ("chamber-pressure", 5e6, "Chamber pressure in Pa"),
        ("exit-pressure", 5e4, "Exit pressure in Pa"),
        ("ambient-pressure", 5e4, "Ambient pressure in Pa"),
        ("temperature", 3600, "Chamber temperature in K"),
        ("mass-flow", 100, "Mass flow in kg/s"),
        ("molecular-weight", 24, "Molecular weight in kg/kmol"),
        ("gamma", 1.2, "Specific heat ratio")]:
        n.add_argument(f"--{name}", type=float, default=default, help=f"{help_text} (default: {default})")
    a = commands.add_parser("analyze", help="Integrate a time/thrust CSV")
    a.add_argument("input", type=Path)
    a.add_argument("--time-column", default="Time", help="Time column, in seconds")
    a.add_argument("--thrust-column", default="Thrust")
    a.add_argument("--thrust-unit", choices=["N", "lbf"], default="N")
    a.add_argument("--propellant-mass", type=float, help="Consumed propellant mass in kg")
    a.add_argument("--limit", type=int, help="Analyze only the first N data rows")
    a.add_argument("--plot", type=Path, help="Save a plot (requires the plot extra)")
    g = commands.add_parser("grain", help="Export legacy illustrative grain curves as CSV")
    g.add_argument("--samples", type=int, default=10)
    g.add_argument("--plot", type=Path, help="Save a plot (requires the plot extra)")
    for command in [n, a, g]:
        command.add_argument("--output", type=Path, help="Output file (default: stdout)")
    for command in [n, a]:
        command.add_argument("--format", choices=["text", "json"], default="text")
    return root


from .data import read_curve




def main(argv=None):
    root = parser()
    args = root.parse_args(argv)
    try:
        if args.command in {None, "shell", "run", "simulate", "simulation", "catalog"}:
            from .calculations import CATALOG, describe
            from .config import Configuration
            from .shell import execute, launch, write_result
            if args.command == "catalog":
                print(describe(args.name) if args.name else "\n".join(sorted(CATALOG)))
                return 0
            config = Configuration(args.config) if args.config else None
            if args.command in {None, "shell"}:
                return launch(config)
            result = execute(config, getattr(args, "name", None), args.command in {"simulate", "simulation"})
            if args.field and not args.plot:
                raise ValueError('--field requires --plot')
            if args.plot:
                if args.plot.resolve() in config.protected_paths() or args.output and args.plot.resolve() == args.output.resolve():
                    raise ValueError('plot must differ from configuration, input, and result files')
                plot_result(result, args.plot, args.field)
            text = write_result(result, args.output, config)
            if text:
                print(text, end="")
            return 0
        if args.command == "analyze":
            for destination in [args.output, args.plot]:
                if destination and destination.resolve() == args.input.resolve():
                    raise ValueError("output paths must differ from the input CSV")
        if getattr(args, "plot", None) and args.output and args.plot.resolve() == args.output.resolve():
            raise ValueError("plot and data output paths must differ")
        if args.command == "nozzle":
            result = nozzle(**{name: getattr(args, name) for name in [
                "chamber_pressure", "exit_pressure", "ambient_pressure", "temperature",
                "mass_flow", "molecular_weight", "gamma"]})
        elif args.command == "analyze":
            time, thrust = read_curve(args)
            result = analyze(time, thrust, args.propellant_mass)
            if args.plot:
                plot_result({"calculation": "analyze", "result": {"history": [dict(time_s=t, thrust_n=f) for t, f in zip(time, thrust)]}}, args.plot)
        else:
            rows = grain_curves(args.samples)
            if args.plot:
                plot_result({"calculation": "grain", "result": rows}, args.plot)
        stream = args.output.open("w", encoding="utf-8", newline="") if args.output else sys.stdout
        try:
            if args.command == "grain":
                writer = csv.writer(stream)
                writer.writerow(["time_s", "progressive", "neutral", "regressive"])
                writer.writerows(rows)
            elif args.format == "json":
                stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
            else:
                stream.write("\n".join(f"{key}: {value:.8g}" for key, value in result.items()) + "\n")
        finally:
            if args.output:
                stream.close()
    except (OSError, ValueError, OverflowError) as exc:
        root.error(str(exc))
    return 0
