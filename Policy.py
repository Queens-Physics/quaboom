class Policy:
    '''
    Handles all of the metrics that would be dealt with by policy, including mask mandates, quarantines, testing, 
    and travel/lockdowns. 
    Initalized once for the entire simulation. 
    
    '''
    
    def __init__(self, sim_obj):
        
        self.sim_obj = sim_obj
        
        # Set the triggers and mandates
        self.mask_mandate = bool(sim_obj.initial_mask_mandate)
        self.mask_trigger = sim_obj.mask_trigger if sim_obj.mask_trigger!=0 else None     
        self.mask_day_trigger = sim_obj.mask_day_trigger if sim_obj.mask_day_trigger!=0 else None
        
        self.lockdown_mandate = bool(sim_obj.initial_lockdown_mandate)
        self.lockdown_trigger = sim_obj.lockdown_trigger if sim_obj.lockdown_trigger!=0 else None
        self.lockdown_day_trigger = sim_obj.lockdown_day_trigger if sim_obj.lockdown_day_trigger!=0 else None
        
        self.initial_testing_mandate = bool(sim_obj.initial_testing_mandate)
        self.testing_trigger = sim_obj.testing_trigger if sim_obj.testing_trigger!=0 else None
        self.testing_day_trigger = sim_obj.testing_day_trigger if sim_obj.testing_day_trigger!=0 else None
        
        self.testing_rate = sim_obj.testing_rate
        self.testing_baseline = sim_obj.testing_baseline
        
    def update_mask_mandate(self, day):
        # Change the policy based on conditions
        if self.mask_day_trigger is not None and day >= self.mask_day_trigger:
            mask_mandate = True
        elif self.mask_trigger is not None and self.sim_obj.pop.count_infected()/self.sim_obj.nPop > self.mask_trigger:
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
        elif self.lockdown_trigger is not None and self.sim_obj.pop.count_infected()/self.sim_obj.nPop > self.lockdown_trigger:
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
        elif self.testing_trigger is not None and self.sim_obj.pop.count_infected()/self.sim_obj.pop.nPop > self.testing_trigger: 
            testing = True
        else:
            testing = False
        return testing
    
    def get_num_tests(self, wait_list):  
        tests = int(self.testing_rate*self.sim_obj.pop.count_quarantined()) # number of tests
        if (tests < self.testing_baseline and wait_list > 0): 
            tests = self.testing_baseline
        return tests
    
    
    