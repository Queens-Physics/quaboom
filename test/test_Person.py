#!/usr/bin/env python3

import unittest
from pathlib import Path

from cv19.person import Person
from cv19.simulation import Simulation


class TestPerson(unittest.TestCase):
    ''' Class used to test specific aspects of the Person class.

    This code is run for each new pull request within the CV19 repository.

    Note
    ----
    The TestPerson class has not been updated recently, and covers a limited amount of the
    person class funcitonality. Keep this in mind when adding new functionality.
    '''

    def setUp(self):
        ''' Set up method for testing the person class.

        This function is called every time the class is initalized, and creates a single
        simulation object that is used in all of the tests.
        '''
        config_file = str(Path(Path(__file__).parent, "../config_files/main.toml").resolve())
        self.sim_obj = Simulation(config_file)

    def tearDown(self):
        ''' Tear down method for testing the person class.

        Currently not used, this function is called after all unit tests have been run.
        '''

    def test_check_cured(self):
        ''' Method used to test the check_cured method to ensure it is behaving correctly.

        This method goes through various scenarios related to curing individuals in the
        simulation to check that they are either cured or not cured correctly. It also
        checks that values such as recovery day and infected day are set properly.
        '''

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
        person3.infect(day=infected_day, cure_days=cure_days, virus_type='alpha')

        day = infected_day + cure_days
        self.assertTrue(person3.check_cured(day=day))     # Should be cured by infected_day + cure_days
        self.assertFalse(person3.is_infected())           # Should no longer be infected
        self.assertTrue(person3.is_recovered())           # Should be recovered
        self.assertEqual(person3.recovered_day, day)      # Should have the right recovery day

    def test_infect(self):
        ''' Method used to test the infect method to ensure it is behaving correctly.

        This method looks to test for proper performance of the infect function in the person
        class. Specifically, it looks at people who should not be able to get infected, that cure
        days is set properly, and that default parameters work.
        '''

        infected_day, cure_days = 10, 5
        person1 = Person(1, sim_obj=self.sim_obj, infected=False, recovered=False)

        self.assertTrue(person1.infect(day=infected_day, virus_type='alpha'))  # Infection should have worked
        self.assertTrue(person1.is_infected())             # Should be infected
        self.assertFalse(person1.is_recovered())           # Should not be recovered
        self.assertEqual(person1.infected_day, infected_day)              # Should have the right infected day

        person2 = Person(2, sim_obj=self.sim_obj, infected=True, recovered=False)
        self.assertFalse(person2.infect(day=infected_day, virus_type='alpha'))  # Should not get infected - already infected

        person3 = Person(3, sim_obj=self.sim_obj, infected=False, recovered=True)
        self.assertFalse(person3.infect(day=infected_day, virus_type='alpha'))  # Should not get infected - already recovered

        person4 = Person(4, sim_obj=self.sim_obj, infected=False, recovered=False)
        person4.infect(day=infected_day, cure_days=cure_days, virus_type='alpha')
        self.assertEqual(person4.cure_days, cure_days)     # Make sure that cure days is set properly

        person5 = Person(5, sim_obj=self.sim_obj, infected=False, recovered=False)
        person5.infect(day=infected_day, virus_type='alpha')
        self.assertIsNotNone(person5.cure_days)            # Make sure that cure days is set even though no parameter passed


if __name__ == '__main__':
    unittest.main()
