#!/usr/bin/env python

import unittest
# Code to import Person.py from parent directory
import os, sys
sys.path.append("../")
import Person

class TestPerson(unittest.TestCase):
    
    def setUp(self):       # Code that will be run before every test function is executed
        pass
    
    def tearDown(self):    # Code that will be run after every test function is executed
        pass
    
#     def test_init(self):
#         # Should have some exceptions in the init to prohibit bad values
#         pass
    
    def test_check_cured(self):
        
        infected_day, cure_days = 10, 5
        person1 = Person.Person(1, infected=True, infected_day=infected_day, cure_days=cure_days)
        day = infected_day + cure_days
        
        self.assertTrue(person1.check_cured(day=day))     # Should be cured by infected_day + cure_days
        self.assertFalse(person1.is_infected())           # Should no longer be infected
        self.assertTrue(person1.is_recovered())           # Should be recovered
        self.assertEqual(person1.recovered_day, day)      # Should have the right recovery day
        
        person2 = Person.Person(2, infected=True, infected_day=infected_day, cure_days=cure_days)
        day -= 1                                          # Day is one day before infection should be cured
        
        self.assertFalse(person2.check_cured(day=day))    # Should be cured by infected_day + cure_days
        self.assertTrue(person2.is_infected())            # Should no longer be infected
        self.assertFalse(person2.is_recovered())          # Should be recovered
        self.assertEqual(person2.recovered_day, None)     # Should have no recovery day
        
        person3 = Person.Person(3, infected=False)
        person3.infect(day=infected_day, cure_days=cure_days)
        
        day = infected_day + cure_days
        self.assertTrue(person3.check_cured(day=day))     # Should be cured by infected_day + cure_days
        self.assertFalse(person3.is_infected())           # Should no longer be infected
        self.assertTrue(person3.is_recovered())           # Should be recovered
        self.assertEqual(person3.recovered_day, day)      # Should have the right recovery day
        
    def test_infect(self):
        
        infected_day, cure_days = 10, 5
        person1 = Person.Person(1, infected=False, recovered=False)
        
        self.assertTrue(person1.infect(day=infected_day))  # Infection should have worked
        self.assertTrue(person1.is_infected())             # Should be infected
        self.assertFalse(person1.is_recovered())           # Should not be recovered
        self.assertEqual(person1.infected_day, infected_day)              # Should have the right infected day
        
        person2 = Person.Person(2, infected=True, recovered=False)
        self.assertFalse(person2.infect(day=infected_day)) # Should not get infected - already infected
        
        person3 = Person.Person(3, infected=False, recovered=True)
        self.assertFalse(person3.infect(day=infected_day)) # Should not get infected - already recovered MIGHT CHANGE
        
        person4 = Person.Person(4, infected=False, recovered=False)
        person4.infect(day=infected_day, cure_days=cure_days)
        self.assertEqual(person4.cure_days, cure_days)     # Make sure that cure days is set properly
        
        person5 = Person.Person(5, infected=False, recovered=False)
        person5.infect(day=infected_day)
        self.assertIsNotNone(person4.cure_days)            # Make sure that cure days is set even though no parameter passed
        
    def test_infect_others(self):
        # No suscept and try to infect
        Pop = [Person.Person(i) for i in range(15)]
        InfectedIndices = []
        for i in range(len(Pop)):
            Pop[i].infect(day=0)
            InfectedIndices.append(i)
        SusceptIndices = [i for i in range(len(Pop)) if i not in InfectedIndices]
        
        self.assertEqual(0, Pop[0].infect_others(Pop, SusceptIndices, day=5, num_to_infect=1))
        
        # Less than the number trying to infect are suscept
        for _ in range(100): # Loop lots of times due to random nature of infection
            Pop = [Person.Person(i) for i in range(15)]
            InfectedIndices = []
            for i in range(len(Pop)-2):
                Pop[i].infect(day=0)
                InfectedIndices.append(i)
            SusceptIndices = [i for i in range(len(Pop)) if i not in InfectedIndices]
            # Should never infect more than 2
            self.assertTrue(Pop[0].infect_others(Pop, SusceptIndices, day=5, num_to_infect=5) <=2)
            
        # Should never try to infect itself
        for _ in range(100):
            Pop = [Person.Person(i) for i in range(15)]
            InfectedIndices = []
            for i in range(0):
                Pop[i].infect(day=0)
                InfectedIndices.append(i)
            SusceptIndices = [i for i in range(len(Pop)) if i not in InfectedIndices]
            Pop[0].infect_others(Pop, SusceptIndices, day=5, num_to_infect=len(Pop)-1)
            self.assertFalse(Pop[0].index in Pop[0].recent_infections)
    
if __name__ == '__main__':
    unittest.main()
    