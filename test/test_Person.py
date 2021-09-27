#!/usr/bin/env python3

import unittest
from pathlib import Path

from cv19.person import Person
from cv19.simulation import simulation


class TestPerson(unittest.TestCase):

    def setUp(self):       # Code that will be run before every test function is executed
        config_file = str(Path(Path(__file__).parent, "../config_files/main.json").resolve())
        self.sim_obj = simulation(config_file)

    def tearDown(self):    # Code that will be run after every test function is executed
        pass

#     def test_init(self):
#         # Should have some exceptions in the init to prohibit bad values
#         pass

    def test_check_cured(self):

        infected_day, cure_days = 10, 5
        person1 = Person(1, infected=True, sim_obj=self.sim_obj, infected_day=infected_day, cure_days=cure_days)
        day = infected_day + cure_days

        self.assertTrue(person1.check_cured(day=day))     # Should be cured by infected_day + cure_days
        self.assertFalse(person1.is_infected())           # Should no longer be infected
        self.assertTrue(person1.is_recovered())           # Should be recovered
        self.assertEqual(person1.recovered_day, day)      # Should have the right recovery day

        person2 = Person(2, infected=True, sim_obj=self.sim_obj, infected_day=infected_day, cure_days=cure_days)
        day -= 1                                          # Day is one day before infection should be cured

        self.assertFalse(person2.check_cured(day=day))    # Should be cured by infected_day + cure_days
        self.assertTrue(person2.is_infected())            # Should no longer be infected
        self.assertFalse(person2.is_recovered())          # Should be recovered
        self.assertEqual(person2.recovered_day, None)     # Should have no recovery day

        person3 = Person(3, sim_obj=self.sim_obj, infected=False)
        person3.infect(day=infected_day, cure_days=cure_days)

        day = infected_day + cure_days
        self.assertTrue(person3.check_cured(day=day))     # Should be cured by infected_day + cure_days
        self.assertFalse(person3.is_infected())           # Should no longer be infected
        self.assertTrue(person3.is_recovered())           # Should be recovered
        self.assertEqual(person3.recovered_day, day)      # Should have the right recovery day

    def test_infect(self):

        infected_day, cure_days = 10, 5
        person1 = Person(1, sim_obj=self.sim_obj, infected=False, recovered=False)

        self.assertTrue(person1.infect(day=infected_day))  # Infection should have worked
        self.assertTrue(person1.is_infected())             # Should be infected
        self.assertFalse(person1.is_recovered())           # Should not be recovered
        self.assertEqual(person1.infected_day, infected_day)              # Should have the right infected day

        person2 = Person(2, sim_obj=self.sim_obj, infected=True, recovered=False)
        self.assertFalse(person2.infect(day=infected_day)) # Should not get infected - already infected

        person3 = Person(3, sim_obj=self.sim_obj, infected=False, recovered=True)
        self.assertFalse(person3.infect(day=infected_day)) # Should not get infected - already recovered MIGHT CHANGE

        person4 = Person(4, sim_obj=self.sim_obj, infected=False, recovered=False)
        person4.infect(day=infected_day, cure_days=cure_days)
        self.assertEqual(person4.cure_days, cure_days)     # Make sure that cure days is set properly

        person5 = Person(5, sim_obj=self.sim_obj, infected=False, recovered=False)
        person5.infect(day=infected_day)
        self.assertIsNotNone(person5.cure_days)            # Make sure that cure days is set even though no parameter passed

if __name__ == '__main__':
    unittest.main()
