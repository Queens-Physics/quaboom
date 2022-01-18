#!/usr/bin/env python3

import unittest
from pathlib import Path
import numpy as np

from cv19.population import Population
from cv19.simulation import simulation


class TestPopulation(unittest.TestCase):
    ''' Class used to test specific aspects of the Population class.

    This code is run for each new pull request within the CV19 repository.

    Note
    ----
    The TestPopulation class has not been updated recently, and covers a limited amount of the
    population class funcitonality. Keep this in mind when adding new functionality.
    '''
    def setUp(self):
        ''' Set up method for testing the population class.

        This function is called every time the class is initalized, and creates a single
        simulation object that is used in all of the tests.
        '''
        config_file = str(Path(Path(__file__).parent, "../config_files/main.json").resolve())
        self.sim_obj = simulation(config_file)

    def tearDown(self):
        ''' Tear down method for testing the person class.

        Currently not used, this function is called after all unit tests have been run.
        '''

    def test_init(self):
        ''' Method to test the initilization function of the population class.

        This funciton tests the __init__ method for the population class to make sure that
        it returns proper values when initialized with different numbers of infected
        individuals.
        '''
        nPop = self.sim_obj.nPop
        variants = self.sim_obj.variants
        n0 = sum(v_id for _, v_id in variants.items())
        pop = Population(self.sim_obj)

        # Make sure that there are n0 infected, 0 recovered, nPop-n0 susceptible
        self.assertEqual(pop.count_infected(), n0)
        self.assertEqual(pop.count_recovered(), 0)
        self.assertEqual(pop.count_susceptible(), nPop-n0)

        # Make sure variant counts are correct
        for key, value in variants.items():
            self.assertEqual(pop.count_variant_cases(key), value)

    def test_get_count_functions(self):
        ''' Method to test the counting methods of the person class.

        This function focuses on testing the counting functions that are used to return
        tracking values of the population in the simulation on a given day.
        '''
        nPop = self.sim_obj.nPop
        pop = Population(self.sim_obj)

        # Make sure that get and count functions return the same info
        self.assertEqual(pop.count_infected(), len(pop.get_infected()))
        self.assertEqual(pop.count_recovered(), len(pop.get_recovered()))
        self.assertEqual(pop.count_susceptible(), len(pop.get_susceptible()))

        # Make sure get pop returns entire population
        self.assertEqual(len(pop.get_population()), nPop)
        self.assertEqual(pop.get_population_size(), nPop)

        # Make sure the get person works
        i = np.random.choice(nPop)
        self.assertEqual(pop.get_person(index=i).get_index(), i)

    def test_globals(self):
        ''' Method to test the global variables used in the population class.

        This function ensures that the global variables (related to population
        demographics) make sense by checking that they sum to 1.
        '''
        pop = Population(self.sim_obj)

        # Make sure weights and options line up - basically just checks config file
        self.assertEqual(len(pop.age_options), len(pop.age_weights))
        self.assertEqual(len(pop.job_options), len(pop.job_weights))
        self.assertEqual(len(pop.house_options), len(pop.house_weights))
        self.assertEqual(len(pop.isolation_options), len(pop.isolation_weights))

        # Make sure probabilities sum to 1
        roundLevel = 6  # Decimal digits to round

        self.assertEqual(round(sum(pop.age_weights), roundLevel), 1)
        self.assertEqual(round(sum(pop.job_weights), roundLevel), 1)
        self.assertEqual(round(sum(pop.house_weights), roundLevel), 1)
        self.assertEqual(round(sum(pop.isolation_weights), roundLevel), 1)

    def test_infect(self):
        ''' Method to test the infect function of the population class.

        This function ensures that the infection mechanics held in the infect method
        perform as expected. Specifically, it tests that their status is updated correctly
        both in the person class attributes, as well as the population class arrays.
        '''
        pop = Population(self.sim_obj)

        # Infect a susceptible person
        index = pop.get_susceptible()[0]
        self.assertTrue(pop.infect(index=index, day=0, virus_type='alpha'))

        # Check that they are infected
        self.assertTrue(pop.get_person(index=index).is_infected())
        # Check that they are not recovered
        self.assertFalse(pop.get_person(index=index).is_recovered())

        # Infected list should be updated
        self.assertTrue(index in pop.get_infected())
        # Try to manually update the list
        self.assertFalse(pop.update_infected(index=index))

        # Try to infect an infected person now
        pop = Population(self.sim_obj)

        index = pop.get_infected()[0]
        self.assertFalse(pop.infect(index=index, day=0, virus_type='alpha'))

        # Now try to falsly update the infected list
        self.assertFalse(pop.update_infected(index=index))

    def test_cure(self):
        ''' Method to test the cure functionality of the population class.

        This function makes sure that individuals within the population are
        being cured correctly using this function. It tests that all the
        required attributes are changed when cured, and that curing only works
        when the day supplied is past the predetermined length of the infection.
        '''
        pop = Population(self.sim_obj)
        infected_id = pop.get_infected()[0]

        # Try to cure a person on day after infection (should not work)
        self.assertFalse(pop.cure(index=infected_id, day=1))
        # Make sure lists are still right
        self.assertFalse(infected_id in pop.get_recovered())
        self.assertTrue(infected_id in pop.get_infected())
        self.assertFalse(infected_id in pop.get_susceptible())
        # Make sure the person attribute was not changed
        self.assertFalse(pop.get_person(index=infected_id).is_recovered())
        self.assertTrue(pop.get_person(index=infected_id).is_infected())

        # Try to manually update the cured person (should not work, they are not cured)
        self.assertFalse(pop.update_cured(index=infected_id))

        # Try to actually cure someone ready to be cured
        pop = Population(self.sim_obj)
        infected_id = pop.get_infected()[0]

        # Make sure cure function works
        self.assertTrue(pop.cure(index=infected_id, day=40)) # day=40 is long past due infection
        # Make sure lists are right
        self.assertTrue(infected_id in pop.get_recovered())
        self.assertFalse(infected_id in pop.get_infected())
        self.assertFalse(infected_id in pop.get_susceptible())
        # Make sure the person attribute was changed
        self.assertTrue(pop.get_person(index=infected_id).is_recovered())
        self.assertFalse(pop.get_person(index=infected_id).is_infected())

if __name__ == '__main__':
    unittest.main()
