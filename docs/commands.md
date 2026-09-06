# Commands and plotting

## Batch commands

Run `pyrocket --help` or `pyrocket COMMAND --help` for argument details.
`python -m PyRocket` uses the same interface.

| Command | Behavior |
| --- | --- |
| `pyrocket` or `pyrocket shell` | Enter the interactive environment |
| `pyrocket --config FILE` | Enter the environment with a loaded TOML file |
| `pyrocket run FILE NAME` | Run a configured name or uniquely matching type |
| `pyrocket run FILE` | Run the full configured simulation |
| `pyrocket simulate FILE` | Run motor, flight, or motor followed by flight |
| `pyrocket catalog` | List available calculation types |
| `pyrocket catalog TYPE` | Show a type's signature and documentation |
| `pyrocket nozzle` | Ideal nozzle sizing with flags and built-in defaults |
| `pyrocket analyze CSV` | Integrate time/thrust data |
| `pyrocket grain` | Export illustrative grain curves as CSV |

`simulation` is an alias for `simulate`. TOML `run` and `simulate` return JSON
and accept `--output PATH`, `--plot PATH`, and `--field FIELD` (requires `--plot`).
The standalone `nozzle` and `analyze` commands accept `--format text|json`;
`grain` writes CSV. Standalone `analyze` and `grain` accept `--plot PATH`.
There is no batch `flight` subcommand; use `simulate` with a flight configuration.

## Interactive commands

The prompt is `pyrocket>`. Command paths with spaces can be quoted.

| Command | Behavior |
| --- | --- |
| `load FILE`, `reload` | Load a file or reread the active file |
| `list`, `ls` | List configured calculations and simulation sections |
| `show [NAME\|simulation\|flight]` | Inspect configuration values |
| `catalog [FILTER]` | List types, optionally filtered by substring |
| `describe TYPE`, `help TYPE` | Inspect calculation parameters |
| `run [FILE] NAME [--output PATH]` | Run a configured calculation |
| `run FILE` | Run that file's full simulation |
| `simulate [FILE] [--output PATH]` | Run the active or supplied simulation |
| `save PATH` | Save the last successful result envelope |
| `plot [PATH] [FIELD]` | Show or save a curve from the last result |
| `plot --field FIELD` | Show a selected field in a window |
| `help`, `exit`, `quit` | Command help or exit; Ctrl-D also exits |

A configured name or a unique type can be entered directly, such as `nozzle`
or `mach`. Ambiguous types report the matching names. With a `[flight]` table,
`flight` runs the full configured simulation, including `[simulation]` if present.
Successful execution of a supplied file makes it the active configuration.
Failed loads and calculations preserve the previous session state. `ls` lists
configuration entries, not filesystem contents. Positional output paths remain
accepted by `run` and `simulate`; prefer explicit `--output PATH`.

## Results, paths and errors

A calculation envelope has `calculation` and `result` keys, plus optional
`messages` containing historical diagnostics. Motor and flight results contain
`summary` and `history`; coupled flight also contains `motor`. The prompt prints
summaries instead of full histories. `save` writes the complete last result.

Input CSV paths in TOML are relative to that TOML file. Command-line and shell
paths are relative to the working directory. Parent output directories must
exist. Existing output files are replaced. Configured input CSVs and the loaded
TOML are protected from plot/result overwrites. Batch commands reject using the
same destination for JSON and plot outputs. Invalid inputs normally produce
exit status 2 in batch mode; the shell prints the error and remains open.

## Plot types

Install the `plot` extra. File export supports PNG, SVG and PDF without a GUI.
Window display needs a usable Matplotlib GUI backend and returns to the prompt
when the window closes.

| Result | Default plot | Field choices |
| --- | --- | --- |
| Motor | Thrust vs time | Any numeric history field except `time_s` |
| Flight | Altitude vs time | Numeric history fields, or `trajectory` for x vs y |
| CSV analysis | Thrust vs time | `thrust_n` |
| Grain curves | All three curves | `progressive`, `neutral`, `regressive` |
| Flat historical array | Values vs sample index | No field selection |
| Scalar or scalar dictionary | No curve available | Use a time history instead |

Examples of motor fields: `chamber_pressure_pa`, `mass_flow_kg_s`,
`propellant_mass_kg`, `throat_area_m2`, `total_impulse_n_s`. Flight fields include
`altitude_m`, `speed_m_s`, `pitch_rad`, `mass_kg`, `thrust_n`, and
`ambient_pressure_pa`.
A coupled result's plot selects flight history. To plot its motor history through
Python, wrap `result['result']['motor']` as a `simulation` result envelope.

For a drag-enabled Earth run, plot `drag_n`, `mach_number`, or
`dynamic_pressure_pa`, for example:

```bash
pyrocket simulate examples/earth-flight.toml --plot earth-drag.png --field drag_n
```
