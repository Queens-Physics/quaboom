class Policy:
    '''
    Handles all of the metrics that would be dealt with by policy, including mask mandates, quarantines, testing, 
    and travel/lockdowns. 
    Initalized once for the entire simulation. 
    
    Parameters
    ----------
    sim_obj : dict
        The configuration details for this class

    Attributes
    ----------
    test_param : string
        Lorem ipsum blah blah blah
    '''

    def __init__(self, sim_obj):
        self.sim_obj = sim_obj
        
        # Set attributes
        self.load_attributes_from_sim_obj()
        
    def load_attributes_from_sim_obj(self):
        # Loop through keys
        attributes = self.sim_obj.parameters["policy_data"].keys()

        for attr in attributes:
            setattr(self, attr, self.sim_obj.parameters["policy_data"][attr])
        
    def update_mask_mandate(self, day):
        """Updates the mask mandate for this day

        Parameters
        ----------
        day : int
            The current day
        
        """

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
        """Gets whether there is currently a mask mandate.

        Returns
        -------
        mask_mandate : bool
            Whether there is currently a mask mandate
        """

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
        """Returns whether or not there is a mandated lockdown.

        Returns
        -------
        lockdown_mandate : bool
            Whether there is currently a lockdown mandate.
        
        """

        return self.lockdown_mandate
    
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

        if (self.testing_baseline == None): 
            self.testing_baseline = 0
        elif (tests < self.testing_baseline and wait_list > 0): 
            tests = self.testing_baseline
        return tests
    
    def check_students(self, day):
        # Change the policy based on conditions
        if self.student_day_trigger is not None and day >= self.student_day_trigger:
            student_mandate = True
        else:
            student_mandate = False
            
        # Actually change the conditions
        self.student_mandate = student_mandate
        return student_mandate

    def get_students_mandate(self):
        return self.student_mandate
