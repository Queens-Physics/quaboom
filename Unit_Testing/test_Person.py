import unittest
# Code to import Person.py from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath("Person.py"))))
import Person

class TestPerson(unittest.TestCase):
    
    def test_