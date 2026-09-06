"""Interactive application session and configuration execution."""
import cmd
import json
from pathlib import Path
import shlex

from .calculations import CATALOG, calculate, describe
from .config import Configuration


from .workflows import execute


def write_result(result, output=None, config=None):
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if output:
        path = Path(output).resolve()
        if config and path in config.protected_paths():
            raise ValueError('output must differ from the configuration and input files')
        path.write_text(text, encoding='utf-8')
    else:
        return text


class BallisticsShell(cmd.Cmd):
    intro = ('PyRocket. Type help for commands.\n'
             'Start with load examples/motor.toml, or simulate examples/motor.toml.\n'
             'Use list for configured calculations; catalog lists available types.')
    prompt = 'pyrocket> '

    def __init__(self, config=None, stdin=None, stdout=None):
        super().__init__(stdin=stdin, stdout=stdout)
        self.config = config
        self.last_result = None
        if stdin is not None:
            self.use_rawinput = False

    def emptyline(self):
        pass

    def do_help(self, line):
        'help [COMMAND|TYPE]: Show shell commands or calculation parameters.'
        name = line.strip()
        if name in CATALOG and name != 'simulation':
            self.stdout.write(describe(name) + '\nRun with: run ' + name + '\n')
            return
        super().do_help(line)
        if not name:
            self.stdout.write('Configured names and unique types are also commands: nozzle, mach, or run NAME.\n'
                              'run FILE.toml / simulate FILE.toml loads and runs a simulation.\n'
                              'Use --output PATH to save results; list (ls) shows configured names.\n')

    def default(self, line):
        tokens = shlex.split(line)
        if tokens and (tokens[0] in CATALOG or
                       self.config and tokens[0] in self.config.calculations):
            return self.do_run(line)
        raise ValueError('unknown command; use help, list (configured calculations), or catalog (types)')

    def onecmd(self, line):
        try:
            return super().onecmd(line)
        except (OSError, ValueError) as exc:
            self.stdout.write(f'Error: {exc}\n')
        except KeyboardInterrupt:
            self.stdout.write('Calculation interrupted.\n')

    def require_config(self):
        if self.config is None:
            raise ValueError('load a TOML file first: load examples/motor.toml')
        return self.config

    def do_load(self, line):
        'load PATH: Load and validate a TOML file. Paths with spaces may be quoted.'
        tokens = shlex.split(line)
        if len(tokens) != 1:
            raise ValueError('usage: load PATH')
        config = Configuration(tokens[0])
        self.config = config
        self.last_result = None
        self.stdout.write(f'Loaded {config.path}\n')

    def do_reload(self, line):
        'reload: Reload the current TOML file after editing it.'
        if line.strip():
            raise ValueError('usage: reload')
        self.do_load(shlex.quote(str(self.require_config().path)))

    def do_list(self, line):
        'list: List the named calculations and simulation in the loaded file.'
        if line.strip():
            raise ValueError('usage: list (or ls)')
        config = self.require_config()
        for name, entry in config.calculations.items():
            self.stdout.write(f'{name}: {entry["type"]}\n')
        if config.flight is not None:
            self.stdout.write('flight: configured planar flight; simulate: full motor/flight run\n')
        if config.simulation is not None:
            self.stdout.write('simulate: coupled SI motor burn simulation\n')

    do_ls = do_list

    def do_catalog(self, line):
        'catalog [FILTER]: List available calculation types, including legacy versions.'
        self.stdout.write('Calculation types: run TYPE uses a unique matching configured entry.\n'
                          'Use list for configured names, or describe TYPE for parameters.\n')
        for name in sorted(CATALOG):
            if line.strip() in name:
                self.stdout.write(name + '\n')

    def do_describe(self, line):
        'describe TYPE: Show the parameters and documentation for a calculation type.'
        self.stdout.write(describe(line.strip()) + '\n')

    def do_show(self, line):
        'show [NAME|simulation]: Show the loaded configuration or a named section.'
        config = self.require_config()
        name = line.strip()
        if not name:
            value = {'calculations': config.calculations, 'simulation': config.simulation, 'flight': config.flight}
        elif name == 'simulation':
            value = config.simulation
        elif name == 'flight':
            value = config.flight
        else:
            kind, parameters = config.calculation(name)
            value = {'type': kind, 'parameters': parameters}
        self.stdout.write(json.dumps(value, indent=2) + '\n')

    def do_run(self, line):
        'run [CONFIG.toml] NAME [--output PATH]: Run a configured name or unique type. A file alone runs its simulation.'
        args = shlex.split(line)
        args, output = self.output_argument(args)
        config = self.config
        if args and args[0].lower().endswith('.toml'):
            config = Configuration(args.pop(0))
        if len(args) == 2 and output is None:  # Original positional output syntax
            output = args.pop()
        if len(args) > 1 or (not args and config is self.config):
            raise ValueError('usage: run [CONFIG.toml] NAME [--output PATH]; run CONFIG.toml runs its simulation')
        result = execute(config, args[0] if args else None)
        self.publish(result, output, config)

    @staticmethod
    def output_argument(args):
        if '--output' not in args:
            return args, None
        index = args.index('--output')
        if index != len(args) - 2:
            raise ValueError('--output must be followed by one output path at the end')
        return args[:index], args[-1]

    def do_simulate(self, line):
        'simulate [CONFIG.toml] [--output PATH]: Run a motor simulation. simulation is an alias.'
        args, output = self.output_argument(shlex.split(line))
        config = self.config
        if args and args[0].lower().endswith('.toml'):
            config = Configuration(args.pop(0))
        if len(args) == 1 and output is None:  # Original positional output syntax
            output = args.pop()
        if len(args) > 1:
            raise ValueError('usage: simulate [CONFIG.toml] [--output PATH]')
        if args:
            raise ValueError('unexpected argument; use simulate [CONFIG.toml] [--output PATH]')
        result = execute(config, simulation=True)
        self.publish(result, output, config)

    do_simulation = do_simulate

    def publish(self, result, output, config=None):
        config = config or self.config
        if output:
            write_result(result, output, config)
            self.stdout.write(f'Saved {output}\n')
        self.config = config
        self.last_result = result
        value = result['result']
        if isinstance(value, dict) and 'history' in value:
            self.stdout.write(json.dumps(value.get('summary', {k: v for k, v in value.items() if k != 'history'}), indent=2) + '\n')
        elif not output:
            self.stdout.write(write_result(result))

    def do_save(self, line):
        'save OUTPUT.json: Save the full result of the last successful calculation.'
        args = shlex.split(line)
        if len(args) != 1:
            raise ValueError('usage: save OUTPUT.json')
        if self.last_result is None:
            raise ValueError('run a calculation first')
        write_result(self.last_result, args[0], self.config)
        self.stdout.write(f'Saved {args[0]}\n')

    def do_plot(self, line):
        'plot [OUTPUT.png] [FIELD]: Show or save the last curve. Use --field FIELD when showing a window.'
        from .plotting import plot_result
        args = shlex.split(line)
        field = None
        if '--field' in args:
            index = args.index('--field')
            if index != len(args) - 2:
                raise ValueError('usage: plot [OUTPUT.png] --field FIELD')
            field = args[-1]
            args = args[:index]
        if len(args) > 2 or len(args) == 2 and field:
            raise ValueError('usage: plot [OUTPUT.png] [FIELD]')
        if len(args) == 2:
            field = args.pop()
        path = Path(args[0]).resolve() if args else None
        if path and path in self.require_config().protected_paths():
            raise ValueError('plot must differ from the configuration and input files')
        plot_result(self.last_result, path, field)
        if path:
            self.stdout.write(f'Saved {path}\n')

    def do_exit(self, line):
        'exit: Leave the application.'
        return True

    do_quit = do_exit
    do_EOF = do_exit


def launch(config=None):
    shell = BallisticsShell(config)
    while True:
        try:
            shell.cmdloop()
            return 0
        except KeyboardInterrupt:
            shell.stdout.write('\nUse exit to leave the application.\n')
            shell.intro = None
