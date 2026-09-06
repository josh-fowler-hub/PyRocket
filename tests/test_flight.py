import math
import subprocess
import sys
from pathlib import Path
import unittest

import PyRocket
from PyRocket.flight import simulate, gimbal_angle
from PyRocket.workflows import execute

ROOT = Path(__file__).resolve().parents[1]


class FlightTest(unittest.TestCase):
    def test_import_is_quiet(self):
        result = subprocess.run([sys.executable, '-c',
            "import PyRocket, sys; assert 'matplotlib.pyplot' not in sys.modules; assert 'PyRocket.shell' not in sys.modules"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')

    def test_circular_coast_conserves_energy(self):
        radius = 3389500.0 + 100000
        mu = 6.67408e-11 * 6.39e23
        result = simulate(thrust_n=0, initial_altitude_m=100000,
                          initial_vy_m_s=math.sqrt(mu/radius), time_step_s=2, max_time_s=200,
                          planet_mass_kg=6.39e23, planet_radius_m=3389500.0, atmosphere='vacuum')
        energy = []
        for row in result['history']:
            r = math.hypot(row['x_m'],row['y_m'])
            energy.append(row['speed_m_s']**2/2-mu/r)
        self.assertAlmostEqual(energy[-1]/energy[0], 1, places=10)
        self.assertAlmostEqual(result['history'][-1]['altitude_m'],100000, places=4)

    def test_cutoff_and_mass_floor(self):
        result = simulate(initial_mass_kg=100, dry_mass_kg=99, thrust_n=1000,
                          specific_impulse_s=100, burn_time_s=20,
                          target_pitch_rad=0, max_time_s=2, time_step_s=.2)
        self.assertAlmostEqual(result['summary']['burn_cutoff_s'],.981)
        self.assertAlmostEqual(result['history'][-1]['mass_kg'],99)
        self.assertEqual(result['history'][-1]['thrust_n'],0)
        self.assertTrue(all(r['mass_kg'] >= 99 for r in result['history']))

    def test_surface_impact_stops(self):
        result = simulate(thrust_n=0, initial_altitude_m=10, max_time_s=20)
        self.assertEqual(result['summary']['termination'],'impact')
        self.assertEqual(result['history'][-1]['altitude_m'],0)
        self.assertLess(result['summary']['duration_s'],20)

    def test_motor_handoff(self):
        config = PyRocket.load(ROOT/'examples/motor-flight.toml')
        config.flight['max_time_s'] = 20
        result = PyRocket.run(config)['result']
        motor = result['motor']
        self.assertAlmostEqual(result['history'][0]['mass_kg'],
                               5+motor['summary']['initial_propellant_mass_kg'])
        self.assertAlmostEqual(result['history'][0]['thrust_n'],motor['history'][0]['thrust_n'])
        self.assertAlmostEqual(result['history'][-1]['mass_kg'],5)
        self.assertEqual(result['history'][-1]['thrust_n'],0)

    def test_incomplete_motor_rejected(self):
        config = PyRocket.load(ROOT/'examples/motor-flight.toml')
        config.simulation['max_steps']=1
        with self.assertRaisesRegex(ValueError,'reach burnout'):
            execute(config)

    def test_pitch_limit_and_invalid_input(self):
        self.assertEqual(gimbal_angle(0,0,0,100,1,0,0,.5),.5)
        for kwargs in [{'dry_mass_kg':0}, {'initial_mass_kg':1}, {'max_steps':True},
                       {'time_step_s':float('nan')}, {'motor_history':[]}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                simulate(**kwargs)

    def test_step_convergence(self):
        a=simulate(max_time_s=10,time_step_s=.1)['history'][-1]
        b=simulate(max_time_s=10,time_step_s=.05)['history'][-1]
        self.assertAlmostEqual(a['altitude_m'],b['altitude_m'],delta=.01)
        self.assertAlmostEqual(a['pitch_rad'],b['pitch_rad'],delta=1e-5)


if __name__ == '__main__':
    unittest.main()
