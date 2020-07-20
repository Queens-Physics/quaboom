#!/usr/bin/env python

import unittest
# Code to import Person.py from parent directory
import os, sys
sys.path.append("../")
import Population
import numpy as np

class TestPopulation(unittest.TestCase):
     
    def setUp(self):       # Code that will be run before every test function is executed
        # Create a pop of 20 people with 5 infected
        nPop = 20
        n0 = 5
        pop = Population.Population(nPop=20, n0=5, ageDistrubution=np.ones(10), jobDistrubution=None, 
                                    householdDistribution=np.ones(6), isolationArray=np.ones(10))
        pass
    
    def tearDown(self):    # Code that will be run after every test function is executed
        pass
    
    def test_init(self):
        
        # Susceptible + infected + recovered = total population
        nInfected = len(pop.infected)
        nSusceptible = len(pop.susceptible)
        nRecovered = len(pop.recovered)
        self.assertEqual(nPop, nInfected + nSusceptible + nRecovered)
        
        # sum(people in households) = nPop
        householdSum = sum([sum(house) for house in pop.households])
        self.assertEqual(householdSum, nPop)
        
        
        
if __name__ == '__main__':
    unittest.main()