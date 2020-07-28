#!/usr/bin/env python

import numpy as np
import unittest
# Code to import Person.py from parent directory
import os, sys
sys.path.append("../")
import Population

class TestPerson(unittest.TestCase):
    
    def setUp(self):       # Code that will be run before every test function is executed
        pass
    
    def tearDown(self):    # Code that will be run after every test function is executed
        pass
    
    def test_init(self):
        nPop, n0 = 1000, 20
        pop = Population.Population(nPop=nPop, n0=n0)
        
        # Make sure that there are n0 infected, 0 recovered, nPop-n0 susceptible
        self.assertEqual(pop.count_infected(), n0)
        self.assertEqual(pop.count_recovered(), 0)
        self.assertEqual(pop.count_susceptible(), nPop-n0)
        
    def test_get_count_functions(self):
        nPop, n0 = 1000, 20
        pop = Population.Population(nPop=nPop, n0=n0)
        
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
        
        # Make sure weights and options line up
        self.assertEqual(len(Population.AGE_OPTIONS), len(Population.AGE_WEIGHTS))
        self.assertEqual(len(Population.JOB_OPTIONS), len(Population.JOB_WEIGHTS))
        self.assertEqual(len(Population.HOUSE_OPTIONS), len(Population.HOUSE_WEIGHTS))
        self.assertEqual(len(Population.ISOLATION_OPTIONS), len(Population.ISOLATION_WEIGHTS))
        
        # Make sure probabilities sum to 1
        roundLevel = 6 # Decimal digits to round 
        self.assertEqual(round(sum(Population.AGE_WEIGHTS), roundLevel), 1)
        self.assertEqual(round(sum(Population.JOB_WEIGHTS), roundLevel), 1)
        self.assertEqual(round(sum(Population.HOUSE_WEIGHTS), roundLevel), 1)
        self.assertEqual(round(sum(Population.ISOLATION_WEIGHTS), roundLevel), 1)
        
if __name__ == '__main__':
    unittest.main()
    