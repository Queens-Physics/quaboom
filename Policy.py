import numpy as np


class Policy:
    '''
    Handles all of the metrics that would be dealt with by policy, including mask mandates, quarantines, testing, 
    and travel/lockdowns. 
    Initalized once for the entire simulation. 
    
    '''
    
    
    def __init__(self, initial_mask_mandate=False, mask_trigger=0.4, mask_day_trigger=None):
        
        # Set the triggers and mandates
        self.mask_mandate = initial_mask_mandate    # Start with no mask requirement
        self.mask_trigger = mask_trigger           # Percent infected to start mask mandate
        self.mask_day_trigger = mask_day_trigger  # A specific day to start wearing masks

        
    def set_simulation(self, population, interaction_sites):
        # These should act like pointers and change with the classes
        self.interaction_sites = interaction_sites
        self.pop = population
        
        self.pop_size = population.get_population_size()
        
    def update_mask_mandate(self, day):
        
        # Change the policy based on conditions
        if self.mask_day_trigger is not None and day >= self.mask_day_trigger:
            mask_mandate = True
        elif self.pop.count_infected()/self.pop_size > self.mask_trigger:
            mask_mandate = True
        else:
            mask_mandate = False
            
        # Actually change the conditions
        self.mask_mandate = mask_mandate
        return mask_mandate
            
    def get_mask_mandate(self):
        return self.mask_mandate


















