import contextlib
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PyRocket.cli import main
from PyRocket.analysis import analyze
from PyRocket.propulsion import grain_curves, nozzle

ROOT = Path(__file__).resolve().parents[1]


class ModelsTest(unittest.TestCase):
    def test_documented_nozzle_example(self):
        result = nozzle(5e6, 5e4, 5e4, 3600, 100, 24, 1.2)
        self.assertAlmostEqual(result['exit_mach'], 3.40, delta=.01)
        self.assertAlmostEqual(result['throat_area_m2'], .0345, delta=.0001)
        self.assertAlmostEqual(result['exit_area_m2'], .409, delta=.001)
        self.assertAlmostEqual(result['thrust_n'], 283200, delta=200)

    def test_integration_and_time_weighted_average(self):
        result = analyze([0, 1, 3], [0, 10, 0], 1)
        self.assertEqual(result['total_impulse_n_s'], 15)
        self.assertEqual(result['average_thrust_n'], 5)
        self.assertAlmostEqual(result['specific_impulse_s'], 15 / 9.80665)

    def test_bad_samples(self):
        for times, forces in [([0], [1]), ([0, 0], [1, 2]), ([1, 0], [1, 2]),
                              ([0, 1], [1, float('nan')])]:
            with self.assertRaises(ValueError):
                analyze(times, forces)

    def test_bad_nozzle(self):
        for gamma, pressure in [(1, 5e4), (1.2, 5e6), (float('nan'), 5e4)]:
            with self.assertRaises(ValueError):
                nozzle(5e6, pressure, 5e4, 3600, 100, 24, gamma)

    def test_grain_matches_existing_csv(self):
        with (ROOT / 'data/cylindrical_fuel_grain_thrust.csv').open() as stream:
            expected = [[float(v) for v in row] for row in csv.reader(stream)]
        actual = grain_curves()
        self.assertEqual(len(actual), len(expected))
        for row, reference in zip(actual, expected):
            for value, target in zip(row, reference):
                self.assertAlmostEqual(value, target)


class CliTest(unittest.TestCase):
    def test_module_entrypoint(self):
        result = subprocess.run([sys.executable, '-m', 'PyRocket', 'nozzle', '--format', 'json'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreater(json.loads(result.stdout)['thrust_n'], 0)

    def test_analysis_units_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.csv'
            output = Path(directory) / 'result.json'
            source.write_text('Time,Thrust\n0,10\n2,10\n')
            self.assertEqual(main(['analyze', str(source), '--thrust-unit', 'lbf',
                                   '--format', 'json', '--output', str(output)]), 0)
            self.assertAlmostEqual(json.loads(output.read_text())['total_impulse_n_s'], 20 * 4.4482216152605)

    def test_bad_input_has_clean_error(self):
        with contextlib.redirect_stderr(io.StringIO()) as error:
            with self.assertRaises(SystemExit) as raised:
                main(['analyze', str(ROOT / 'data/SRM-1.csv'), '--limit', '1'])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn('limit must be at least two', error.getvalue())
        self.assertNotIn('Traceback', error.getvalue())

    def test_input_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.csv'
            content = 'Time,Thrust\n0,1\n1,2\n'
            source.write_text(content)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(['analyze', str(source), '--output', str(source)])
            self.assertEqual(source.read_text(), content)


if __name__ == '__main__':
    unittest.main()
