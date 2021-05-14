#!/usr/bin/env python3

import numpy as np
import unittest
import Population
import simulation as sim

class TestPopulation(unittest.TestCase):
    
    def setUp(self):       # Code that will be run before every test function is executed
        config_file = "./config_files/main_config.json"
        self.sim_obj = sim.simulation(config_file)
        pass
    
    def tearDown(self):    # Code that will be run after every test function is executed
        pass
    
    def test_init(self):
        nPop, n0 = self.sim_obj.nPop, self.sim_obj.n0
        pop = Population.Population(self.sim_obj)
        
        # Make sure that there are n0 infected, 0 recovered, nPop-n0 susceptible
        self.assertEqual(pop.count_infected(), n0)
        self.assertEqual(pop.count_recovered(), 0)
        self.assertEqual(pop.count_susceptible(), nPop-n0)
        
    def test_get_count_functions(self):
        nPop, n0 = self.sim_obj.nPop, self.sim_obj.n0
        pop = Population.Population(self.sim_obj)
        
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
        nPop, n0 = self.sim_obj.nPop, self.sim_obj.n0
        pop = Population.Population(self.sim_obj)
        
        # Make sure weights and options line up - basically just checks config file
        self.assertEqual(len(pop.age_options), len(pop.age_weights))
        self.assertEqual(len(pop.job_options), len(pop.job_weights))
        self.assertEqual(len(pop.house_options), len(pop.house_weights))
        self.assertEqual(len(pop.isolation_options), len(pop.isolation_weights))
        
        # Make sure probabilities sum to 1
        roundLevel = 6 # Decimal digits to round 
        self.assertEqual(round(sum(pop.age_weights), roundLevel), 1)
        self.assertEqual(round(sum(pop.job_weights), roundLevel), 1)
        self.assertEqual(round(sum(pop.house_weights), roundLevel), 1)
        self.assertEqual(round(sum(pop.isolation_weights), roundLevel), 1)
        
    def test_infect(self):
        nPop, n0 = self.sim_obj.nPop, self.sim_obj.n0
        pop = Population.Population(self.sim_obj)
        
        # Infect a susceptible person
        index = pop.get_susceptible()[0]
        self.assertTrue(pop.infect(index=index, day=0))
        
        # Check that they are infected
        self.assertTrue(pop.get_person(index=index).is_infected())
        # Check that they are not recovered
        self.assertFalse(pop.get_person(index=index).is_recovered())

        # Infected list should be updated
        self.assertTrue(index in pop.get_infected())
        # Try to manually update the list
        self.assertFalse(pop.update_infected(index=index))
        
        # Try to infect an infected person now
        nPop, n0 = self.sim_obj.nPop, self.sim_obj.n0
        pop = Population.Population(self.sim_obj)
        
        index = pop.get_infected()[0]
        self.assertFalse(pop.infect(index=index, day=0))
        
        # Now try to falsly update the infected list
        self.assertFalse(pop.update_infected(index=index))
        
    def test_cure(self):
        nPop, n0 = self.sim_obj.nPop, self.sim_obj.n0
        pop = Population.Population(self.sim_obj)
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
        nPop, n0 = self.sim_obj.nPop, self.sim_obj.n0
        pop = Population.Population(self.sim_obj)
        infected_id = pop.get_infected()[0]
        
        # Make sure cure function works
        self.assertTrue(pop.cure(index=infected_id, day=40)) #day=40 is long past due infection
        # Make sure lists are right
        self.assertTrue(infected_id in pop.get_recovered())
        self.assertFalse(infected_id in pop.get_infected())
        self.assertFalse(infected_id in pop.get_susceptible())
        # Make sure the person attribute was changed
        self.assertTrue(pop.get_person(index=infected_id).is_recovered())
        self.assertFalse(pop.get_person(index=infected_id).is_infected())

if __name__ == '__main__':
    unittest.main()
