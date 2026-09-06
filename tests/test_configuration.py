import io
import json
from pathlib import Path
import tempfile
import unittest

from PyRocket.calculations import CATALOG, calculate
from PyRocket.config import Configuration
from PyRocket.shell import BallisticsShell, execute, write_result
from PyRocket.propulsion.motor import mach_from_area, simulate

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/motor.toml'


class ConfigurationTest(unittest.TestCase):
    def test_relative_input_and_calculation(self):
        config = Configuration(EXAMPLE)
        result = execute(config, 'static_fire')['result']
        self.assertEqual(result['samples'], 265)
        self.assertGreater(result['total_impulse_n_s'], 0)
        self.assertEqual(Path(config.calculations['static_fire']['parameters']['input']), ROOT / 'data/SRM-1.csv')

    def test_all_historical_functions_available(self):
        expected = json.loads((ROOT / 'tests/fixtures/legacy_catalog.json').read_text())
        for version, names in expected.items():
            for name in names:
                self.assertIn(f'legacy.{version}.{name}', CATALOG)

    def test_reject_invalid_config(self):
        cases = ['version = 2', 'version = 1\nunknown = 2',
                 'version = 1\n[calculations.x]\ntype = "unknown"',
                 'version = 1\n[calculations.x]\ntype = "mach"\n[calculations.x.parameters]\narea_ratio=2.0',
                 'version = 1\n[calculations.x]\ntype = "grain"\n[calculations.x.parameters]\nsampels=2',
                 'version = 1\n[calculations.x]\ntype = "grain"\n[calculations.x.parameters]\nsamples=nan']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.toml'
            for content in cases:
                path.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    Configuration(path)

    def test_output_protects_inputs(self):
        config = Configuration(EXAMPLE)
        for path in config.protected_paths():
            with self.assertRaises(ValueError):
                write_result({'result': 1}, path, config)

    def test_session_recovery_and_save(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            commands = f'run missing\nload "{EXAMPLE}"\nrun missing\nrun exit_mach\nsave "{output}"\nexit\n'
            stdout = io.StringIO()
            shell = BallisticsShell(stdin=io.StringIO(commands), stdout=stdout)
            shell.cmdloop()
            self.assertEqual(stdout.getvalue().count('Error:'), 2)
            self.assertGreater(json.loads(output.read_text())['result'], 1)

    def test_failed_reload_preserves_session(self):
        shell = BallisticsShell(Configuration(EXAMPLE), stdout=io.StringIO())
        shell.onecmd('load /does/not/exist.toml')
        self.assertEqual(shell.config.path, EXAMPLE)


class SimulationTest(unittest.TestCase):
    def setUp(self):
        self.parameters = Configuration(EXAMPLE).simulation.copy()

    def test_burnout_and_conservation(self):
        result = simulate(**self.parameters)
        summary, rows = result['summary'], result['history']
        self.assertEqual(summary['termination'], 'burnout')
        self.assertTrue(summary['completed'])
        self.assertAlmostEqual(rows[-1]['propellant_mass_kg'], 0)
        self.assertEqual(rows[-1]['thrust_n'], 0)
        for before, after in zip(rows, rows[1:]):
            self.assertGreater(after['time_s'], before['time_s'])
            self.assertLessEqual(after['propellant_mass_kg'], before['propellant_mass_kg'])
            self.assertAlmostEqual(before['mass_flow_kg_s'], before['chamber_pressure_pa'] * before['throat_area_m2'] / self.parameters['characteristic_velocity_m_s'])
        integrated_mass = sum(r['mass_flow_kg_s'] * (s['time_s'] - r['time_s']) for r, s in zip(rows, rows[1:]))
        self.assertAlmostEqual(integrated_mass, summary['initial_propellant_mass_kg'], delta=.01)

    def test_time_step_convergence(self):
        coarse = simulate(**self.parameters)['summary']
        self.parameters['time_step_s'] /= 2
        fine = simulate(**self.parameters)['summary']
        self.assertAlmostEqual(coarse['duration_s'], fine['duration_s'], delta=.01)
        self.assertAlmostEqual(coarse['total_impulse_n_s'] / fine['total_impulse_n_s'], 1, delta=.005)

    def test_end_burnout(self):
        self.parameters.update(ends_inhibited=False, length_m=.02, ambient_pressure_pa=0)
        result = simulate(**self.parameters)
        self.assertEqual(result['summary']['termination'], 'burnout')
        self.assertAlmostEqual(result['history'][-1]['web_m'], .01)
        self.assertAlmostEqual(result['history'][-1]['propellant_mass_kg'], 0)

    def test_limits_are_not_reported_as_burnout(self):
        for changes, reason in [({'max_time_s': .015}, 'max_time'), ({'max_steps': 1}, 'max_steps')]:
            result = simulate(**(self.parameters | changes))
            self.assertFalse(result['summary']['completed'])
            self.assertEqual(result['summary']['termination'], reason)

    def test_invalid_geometry_and_parameters(self):
        for changes in [{'inner_radius_m': .06}, {'burn_exponent': 1}, {'time_step_s': 0},
                        {'grain_count': True}, {'ends_inhibited': 1}, {'gamma': float('nan')}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                simulate(**(self.parameters | changes))

    def test_mach_branches_and_historical_no_separation(self):
        self.assertEqual(mach_from_area(1, 1.4), 1)
        for subsonic in [True, False]:
            mach = mach_from_area(2, 1.4, subsonic)
            self.assertEqual(mach < 1, subsonic)
            ratio = calculate('legacy.v2.area_rat', {'Mach2s': [mach], 'k': 1.4})['result'][0]
            self.assertAlmostEqual(ratio, 2)
        result = calculate('legacy.v0.C_F', {'k': 1.4, 'area_rats': [1, 2], 'p1_p3': 1000})
        self.assertEqual(len(result['result']), 2)
        with self.assertRaises(ValueError):
            calculate('legacy.v2.M2', {'area_rat': .5, 'k': 1.4})


class CommandConsistencyTest(unittest.TestCase):
    def test_transcript_commands(self):
        output = io.StringIO()
        shell = BallisticsShell(stdout=output)
        shell.onecmd(f'run "{EXAMPLE}"')
        self.assertEqual(shell.last_result['calculation'], 'simulation')
        shell.onecmd('ls')
        self.assertIn('nozzle_example', output.getvalue())
        for command, kind in [('nozzle', 'nozzle'), ('mach', 'mach'),
                              ('simulation', 'simulation'), ('run mach', 'mach')]:
            shell.onecmd(command)
            self.assertEqual(shell.last_result['calculation'], kind)
        shell.onecmd(f'simulate "{EXAMPLE}"')
        self.assertNotIn('Error:', output.getvalue())

    def test_explicit_file_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'saved result.json'
            shell = BallisticsShell(stdout=io.StringIO())
            shell.onecmd(f'run "{EXAMPLE}" mach --output "{path}"')
            self.assertEqual(json.loads(path.read_text())['calculation'], 'mach')
            shell.onecmd(f'simulation "{EXAMPLE}" --output "{path}"')
            self.assertEqual(json.loads(path.read_text())['calculation'], 'simulation')

    def test_ambiguous_type_requires_name(self):
        config = Configuration(EXAMPLE)
        config.calculations['second_mach'] = config.calculations['exit_mach'].copy()
        with self.assertRaisesRegex(ValueError, 'multiple calculations'):
            execute(config, 'mach')
        self.assertEqual(execute(config, 'exit_mach')['calculation'], 'mach')

    def test_file_is_not_treated_as_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'motor.toml'
            content = 'version = 1\n[simulation]\n' + '\n'.join(
                f'{key} = {str(value).lower()}' for key, value in Configuration(EXAMPLE).simulation.items())
            path.write_text(content)
            shell = BallisticsShell(Configuration(EXAMPLE), stdout=io.StringIO())
            shell.onecmd(f'simulate "{path}"')
            self.assertEqual(path.read_text(), content)
            shell.onecmd(f'simulate --output "{path}"')
            self.assertEqual(path.read_text(), content)

    def test_cli_alias_and_file_only_run(self):
        import subprocess
        import sys
        for command in ['simulation', 'run']:
            result = subprocess.run([sys.executable, '-m', 'PyRocket', command, str(EXAMPLE)],
                                    capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['calculation'], 'simulation')


if __name__ == '__main__':
    unittest.main()
