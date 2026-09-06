import math
from pathlib import Path
import unittest
import numpy as np

import PyRocket
from PyRocket.atmosphere import pressure, EARTH_GEOPOTENTIAL_RADIUS_M

ROOT = Path(__file__).resolve().parents[1]


class AtmosphereTest(unittest.TestCase):
    def test_standard_layer_base_pressures(self):
        # USSA1976 lower-atmosphere layer bases, geopotential m and Pa.
        for height, expected in [(0,101325), (11000,22632.06), (20000,5474.89),
                                 (32000,868.02), (47000,110.91), (51000,66.94), (71000,3.9564)]:
            geometric = EARTH_GEOPOTENTIAL_RADIUS_M*height/(EARTH_GEOPOTENTIAL_RADIUS_M-height)
            with self.subTest(height=height):
                self.assertAlmostEqual(pressure(geometric), expected, delta=.01)
                if height:
                    self.assertAlmostEqual(pressure(geometric-.001)/pressure(geometric+.001),1,delta=1e-6)
        self.assertAlmostEqual(pressure(86000), .37338, delta=.0001)

    def test_domain_and_geometric_conversion(self):
        self.assertGreater(pressure(11000),22632.06)
        for value in [-1, 86001, float('nan'), float('inf'), True]:
            with self.assertRaises(ValueError): pressure(value)

    def test_flight_corrects_reference_pressure_without_double_counting(self):
        config=PyRocket.load(ROOT/'examples/earth-flight.toml')
        config.flight['max_time_s']=20
        config.flight['drag_model']='none' # Isolate the pressure-thrust correction
        response=PyRocket.run(config)['result']
        history=response['motor']['history']
        times=[r['time_s'] for r in history]
        for row in response['history']:
            self.assertAlmostEqual(row['ambient_pressure_pa'],pressure(row['altitude_m']),delta=.001)
            if row['time_s'] < times[-1]:
                source=history[max(0,np.searchsorted(times,row['time_s'],side='right')-1)]
                expected=source['thrust_n']+(source['ambient_pressure_pa']-row['ambient_pressure_pa'])*source['exit_area_m2']
                self.assertAlmostEqual(row['thrust_n'],expected)
            else:
                self.assertEqual(row['thrust_n'],0)
        self.assertAlmostEqual(response['history'][0]['thrust_n'],history[0]['thrust_n'])
        vacuum=PyRocket.flight.simulate(**(config.flight | {'atmosphere':'vacuum'}),motor_history=history)
        self.assertGreater(vacuum['history'][-1]['altitude_m'],response['history'][-1]['altitude_m'])

    def test_no_earth_atmosphere_on_mars_or_silent_upper_extrapolation(self):
        with self.assertRaisesRegex(ValueError,'Earth atmosphere'):
            PyRocket.flight.simulate(planet_mass_kg=6.39e23,planet_radius_m=3389500)
        with self.assertRaisesRegex(ValueError,'86000'):
            PyRocket.flight.simulate(initial_altitude_m=90000,max_time_s=1)

    def test_motor_metadata_required(self):
        rows=[{'time_s':0,'thrust_n':100,'propellant_mass_kg':1},
              {'time_s':1,'thrust_n':0,'propellant_mass_kg':0}]
        with self.assertRaisesRegex(ValueError,'exit_area_m2'):
            PyRocket.flight.simulate(motor_history=rows)


if __name__ == '__main__':
    unittest.main()
