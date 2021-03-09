import numpy as np


class Policy:
    '''
    Handles all of the metrics that would be dealt with by policy, including mask mandates, quarantines, testing, 
    and travel/lockdowns. 
    Initalized once for the entire simulation. 
    
    '''
    
    
    def __init__(self, initial_mask_mandate=False, mask_trigger=None, mask_day_trigger=None, 
                 initial_lockdown_mandate=False, lockdown_trigger=None, lockdown_day_trigger=None, tests_per_day=0,testing_trigger=None,testing_day_trigger=None, initial_testing=False):
        
        # Set the triggers and mandates
        self.mask_mandate = initial_mask_mandate          # Start with no mask requirement
        self.mask_trigger = mask_trigger                  # Percent infected to start mask mandate
        self.mask_day_trigger = mask_day_trigger          # A specific day to start wearing masks
        self.lockdown_mandate = initial_lockdown_mandate  # Start with no lockdown requirement
        self.lockdown_trigger = lockdown_trigger          # Percent infected to start lockdown
        self.lockdown_day_trigger = lockdown_day_trigger  # A specific day to start lockdown
        self.tests_per_day = tests_per_day                # Number of tests run per day
        self.testing_trigger = testing_trigger            # Percent infected to start lockdown
        self.testing_day_trigger = testing_day_trigger   # A specific day to start testing
        self.initial_testing = initial_testing
        
    def set_simulation(self, population, interaction_sites):
        # These should act like pointers and change with the classes
        self.interaction_sites = interaction_sites
        self.pop = population
        
        self.pop_size = population.get_population_size()
        
    def update_mask_mandate(self, day):
        # Change the policy based on conditions
        if self.mask_day_trigger is not None and day >= self.mask_day_trigger:
            mask_mandate = True
        elif self.mask_trigger is not None and self.pop.count_infected()/self.pop_size > self.mask_trigger:
            mask_mandate = True
        else:
            mask_mandate = False
            
        # Actually change the conditions
        self.mask_mandate = mask_mandate
        return mask_mandate
            
    def get_mask_mandate(self):
        return self.mask_mandate
    
    def update_lockdown(self, day):
        
        # Change the policy based on conditions
        if self.lockdown_day_trigger is not None and day >= self.lockdown_day_trigger:
            lockdown_mandate = True
        elif self.lockdown_trigger is not None and self.pop.count_infected()/self.pop_size > self.lockdown_trigger:
            lockdown_mandate = True
        else:
            lockdown_mandate = False
            
        # Actually change the conditions
        self.lockdown_mandate = lockdown_mandate
        return lockdown_mandate
            
    def get_lockdown_mandate(self):
        return self.mask_mandate
    
    def update_testing(self,day):
        if self.testing_day_trigger is not None and day >= self.testing_day_trigger: 
            testing = True
        elif self.testing_trigger is not None and self.pop.count_infected()/self.pop_size > self.testing_trigger: 
            testing = True
        else:
            testing = False
        return testing
    
    def get_num_tests(self, delta_wait_list): 
        if delta_wait_list > 0: 
            self.tests_per_day += int(self.tests_per_day*0.1)
        elif delta_wait_list < 0: 
            self.tests_per_day -= int(self.tests_per_day*0.1)
        elif self.tests_per_day < 0: 
            self.tests_per_day = 0
        return self.tests_per_day
