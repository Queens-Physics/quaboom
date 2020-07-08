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
        
#     def test_infect(self):
        
#         infected_day = 10
#         person1 = Person.Person(1, infected=False, recovered=False)
#         person1.infect(day=infected_day)

    
if __name__ == '__main__':
    unittest.main()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    