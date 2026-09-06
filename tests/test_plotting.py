import io
from pathlib import Path
import tempfile
import unittest

from PyRocket.config import Configuration
from PyRocket.shell import BallisticsShell, execute
from PyRocket.plotting import series_for, plot_result

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/motor.toml'


class PlottingTest(unittest.TestCase):
    def test_analysis_uses_time_and_si_force(self):
        result = execute(Configuration(EXAMPLE), 'static_fire')
        x, series, xlabel, ylabel = series_for(result)
        self.assertEqual(len(x), 265)
        self.assertAlmostEqual(series['thrust_n'][0], 258363 * 4.4482216152605)
        self.assertEqual(ylabel, 'Thrust (N)')

    def test_grain_series_and_selection(self):
        result = execute(Configuration(EXAMPLE), 'grain')
        self.assertEqual(len(series_for(result)[1]), 3)
        self.assertEqual(list(series_for(result, 'neutral')[1]), ['neutral'])
        with self.assertRaises(ValueError):
            series_for(result, 'pressure')

    def test_scalar_has_actionable_error(self):
        with self.assertRaisesRegex(ValueError, 'no curve'):
            series_for(execute(Configuration(EXAMPLE), 'mach'))

    def test_save_png_and_svg(self):
        try:
            import matplotlib
        except ImportError:
            self.skipTest('optional Matplotlib is not installed')
        result = execute(Configuration(EXAMPLE), 'grain')
        with tempfile.TemporaryDirectory() as directory:
            png = Path(directory) / 'grain.png'
            svg = Path(directory) / 'grain.svg'
            plot_result(result, png)
            plot_result(result, svg)
            self.assertTrue(png.read_bytes().startswith(b'\x89PNG'))
            self.assertIn('<svg', svg.read_text())

    def test_shell_protects_config_and_recovers(self):
        output = io.StringIO()
        shell = BallisticsShell(Configuration(EXAMPLE), stdout=output)
        shell.onecmd('plot')
        self.assertIn('run a calculation', output.getvalue())
        shell.onecmd('grain')
        shell.onecmd(f'plot "{EXAMPLE}"')
        self.assertIn('must differ', output.getvalue())


if __name__ == '__main__':
    unittest.main()
