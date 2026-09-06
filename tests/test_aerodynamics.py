import unittest
import math
from pathlib import Path
import PyRocket
from PyRocket.flight import drag

ROOT=Path(__file__).resolve().parents[1]


class AerodynamicsTest(unittest.TestCase):
    def test_atmosphere_state(self):
        air=PyRocket.atmosphere.properties(0)
        self.assertEqual(air['temperature_k'],288.15)
        self.assertAlmostEqual(air['density_kg_m3'],1.225,places=4)
        self.assertAlmostEqual(air['speed_of_sound_m_s'],340.294,places=2)
        self.assertEqual(air['pressure_pa'],PyRocket.atmosphere.pressure(0))

    def test_drag_opposes_both_velocity_components(self):
        for vx,vy in [(30,40),(-30,40),(30,-40),(-30,-40)]:
            result=drag(vx,vy,1.2,340,0.1)
            self.assertAlmostEqual(result['drag_n'],22.5)
            self.assertLess(result['drag_x_n']*vx+result['drag_y_n']*vy,0)
        zero=drag(0,0,1.2,340,0.1)
        self.assertEqual(zero['drag_n'],0)
        self.assertEqual(zero['drag_x_n'],0)

    def test_coefficient_branches(self):
        for mach,expected in [(0,.15),(.6,.15),(1.2,.4204),(1.8,.2498),(4,.175)]:
            self.assertAlmostEqual(drag(mach*100,0,1,100,1)['drag_coefficient'],expected)

    def test_flight_drag_lowers_apogee_and_opposes_descent(self):
        config=PyRocket.load(ROOT/'examples/nozzle-to-flight.toml')
        sizing=PyRocket.run(config,'nozzle_design')['result']
        config.simulation.update(throat_radius_m=math.sqrt(sizing['throat_area_m2']/math.pi),
                                 exit_area_m2=sizing['exit_area_m2'],
                                 characteristic_velocity_m_s=sizing['characteristic_velocity_m_s'])
        with_drag=PyRocket.run(config)['result']
        config.flight['drag_model']='none'
        without_drag=PyRocket.run(config)['result']
        self.assertLess(with_drag['summary']['max_altitude_m'],without_drag['summary']['max_altitude_m'])
        for row in with_drag['history']:
            self.assertLessEqual(row['drag_x_n']*row['vx_m_s']+row['drag_y_n']*row['vy_m_s'],0)
        self.assertGreater(with_drag['history'][-1]['drag_x_n'],0)

    def test_invalid_drag(self):
        for changes in [{'drag_model':'unknown'},{'drag_model':'mae540','atmosphere':'vacuum'},
                        {'reference_area_m2':0}]:
            with self.assertRaises(ValueError): PyRocket.flight.simulate(**changes)
        with self.assertRaises(ValueError): drag(1,0,-1,340,1)
