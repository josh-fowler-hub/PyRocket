"""Verify the documented example actually connects the three stages."""
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest

import PyRocket

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('nozzle_to_flight_example', ROOT / 'examples/nozzle_to_flight.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class WorkflowExampleTest(unittest.TestCase):
    def test_design_transfer_and_reusable_configs(self):
        source = ROOT / 'examples/nozzle-to-flight.toml'
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = workflow.run_workflow(source, output, plots=False)
            sizing = result['nozzle']['result']
            motor_config = PyRocket.load(output / 'motor.toml')
            self.assertAlmostEqual(math.pi * motor_config.simulation['throat_radius_m']**2,
                                   sizing['throat_area_m2'])
            self.assertEqual(motor_config.simulation['exit_area_m2'], sizing['exit_area_m2'])
            self.assertEqual(motor_config.simulation['characteristic_velocity_m_s'],
                             sizing['characteristic_velocity_m_s'])
            self.assertEqual(PyRocket.run(motor_config), result['motor'])
            self.assertEqual(PyRocket.run(PyRocket.load(output / 'flight.toml')), result['flight'])
            self.assertTrue(result['motor']['result']['summary']['completed'])
            self.assertEqual(result['flight']['result']['summary']['termination'], 'impact')
            self.assertEqual(result['flight']['result']['motor'], result['motor']['result'])
            self.assertEqual(source.read_bytes(), original)

    def test_incomplete_burn_does_not_write_products(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.toml'
            source.write_text((ROOT / 'examples/nozzle-to-flight.toml').read_text().replace(
                'max_time_s = 120.0', 'max_time_s = 0.01'))
            output = Path(directory) / 'results'
            with self.assertRaisesRegex(ValueError, 'reach burnout'):
                workflow.run_workflow(source, output, plots=False)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
