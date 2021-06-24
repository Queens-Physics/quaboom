class Policy:
    '''
    Handles all of the metrics that would be dealt with by policy, including mask mandates, 
    quarantines, testing, travel/lockdowns, and whether students have entered the simulation.
    
    Initalized once for the entire simulation.
    
    In addition to the major attributes outlined below, this class also contains all of the 
    attributes outlined in the Policy section of the config file used in a given simulation. 
    
    Attributes
    ----------
    sim_obj : :obj:`simulation class`
        A pointer linking the policy class object to the encompassing simulation class object. 
        This allows the policy class to access important simulation class functions such as 
        counting functions for the tracking arrays and population size. 
    '''

    def __init__(self, sim_obj):
        ''' __init__ method docstring.

        Parameters
        ----------
        sim_obj : simulation class object
            The encompassing simulation obejct hosting the simulation. 

        '''

        self.sim_obj = sim_obj

        # Set attributes
        self.load_attributes_from_sim_obj()

    def load_attributes_from_sim_obj(self):
        '''Method to load in attributes from the provided simulation class object.

        Sets all objects in the "policy_data" dictionary key as self
        attributes of the policy class. No paramteres are passed, as 
        the simulation class is set as an attribute. 

        '''
        # Loop through keys
        attributes = self.sim_obj.parameters["policy_data"].keys()

        for attr in attributes:
            setattr(self, attr, self.sim_obj.parameters["policy_data"][attr])

    def update_mask_mandate(self, day):
        '''Method to update the simulation's mask mandate based on trigger parameters.
        
        This funciton evaluates whether masks should be required based on different
        triggering parameters: `mask_day_trigger` and `mask_trigger`. 
        
        If the current day is greater than the `mask_day_trigger` value, masks will 
        be required. 
        
        If the percent of the populaiton showing infected symptoms is greater than 
        `mask_trigger`, masks will be required. 
        
        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.
            Used to evaluate whether the simulation has passed the day trigger.
            
        '''
        # Change the policy based on conditions
        if self.mask_day_trigger is not None and day >= self.mask_day_trigger:
            mask_mandate = True
        elif self.mask_trigger is not None and self.sim_obj.pop.count_infected()/self.prob_of_symptoms/self.sim_obj.nPop > self.mask_trigger:
            mask_mandate = True
        else:
            mask_mandate = False

        # Actually change the conditions
        self.mask_mandate = mask_mandate
        return mask_mandate

    def get_mask_mandate(self):
        '''Method to return the current mask mandate.

        Returns
        -------
        self.mask_mandate : bool
        '''
        return self.mask_mandate


    def update_lockdown(self, day):
        '''Method to update the simulation's lockdown mandate based on trigger parameters.
        
        This funciton evaluates whether lockdown should be enforced based on different
        triggering parameters: `lockdown_on_day_trigger`, 'lockdown_off_day_trigger`, 
        `lockdown_on_trigger` and `lockdown_off_trigger`. 
        
        If the current day is greater than `lockdown_on_day_trigger` and less than
        `lockdown_off_day_trigger`, lockdown will be enforced. 
        
        If the current percent of the population showing infection symptoms is above
        `lockdown_on_trigger` and below `lockdown_off_trigger`, lockdown will be 
        enforced. 
        
        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.
            Used to evaluate whether the simulation has passed the day trigger.
            
        '''

        # Change the policy based on conditions
        if self.lockdown_on_day_trigger is not None and day >= self.lockdown_on_day_trigger:
            lockdown_mandate = True
        elif self.lockdown_on_day_trigger is not None and day >= self.lockdown_off_day_trigger:
            lockdown_mandate = False
        elif self.lockdown_on_trigger is not None and self.sim_obj.pop.count_quarantined()/self.prob_of_symptoms/self.sim_obj.nPop > self.lockdown_on_trigger:
            lockdown_mandate = True
        elif self.lockdown_off_trigger is not None and self.sim_obj.pop.count_quarantined()/self.prob_of_symptoms/self.sim_obj.nPop <= self.lockdown_off_trigger:
            lockdown_mandate = False
        else:
            lockdown_mandate = False

        # Actually change the conditions
        self.lockdown_mandate = lockdown_mandate
        return lockdown_mandate

    def get_lockdown_mandate(self):
        '''Method to return the current lockdown_mandate.

        Returns
        -------
        self.lockdown_mandate : bool
        '''
        return self.lockdown_mandate

    def update_testing(self, day):
        '''Method to update the simulation's testing mandate based on trigger parameters.
        
        This funciton evaluates whether testing should be performed based on different
        triggering parameters: `testing_day_trigger` and `testing_trigger`. 
        
        If the current day is greater than `testing_day_trigger`, lockdown will be enforced. 
        
        If the current percent of the population showing infection symptoms is above
        `testing_trigger`, lockdown will be enforced. 
        
        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.
            Used to evaluate whether the simulation has passed the day trigger.
            
        '''
        
        if self.testing_day_trigger is not None and day >= self.testing_day_trigger:
            testing = True
        elif self.testing_trigger is not None and self.sim_obj.pop.count_quarantined()/self.prob_of_symptoms/self.sim_obj.pop.nPop > self.testing_trigger:
            testing = True
        else:
            testing = False
        return testing

    def get_num_tests(self, wait_list):
        '''A method to calculate how many tests to administer for a given day. 
        
        The number of tests on any given day is assumed to have a linear relationship with 
        the number of people quarantined, the number of people who are just entering
        quarantine, and the number of people joining the quarantine waitlist. 
        
        This funciton uses the `testing_rate` parameter, which is designed as follows:
        testing_rate = [number of tests/people in quarantine, 
                        number of tests/people newly in quarantine, 
                        number of tests/number of people in the waitlist]
                        
        This method also ensures that, at the minimum, the number of tests administered
        is not below the `testing_baseline` parameter. 
                        
        Parameters
        ----------
        wait_list : int
            The number of people on the testing waitlist for this day in the simulation. 
        '''

        tests =  (self.testing_rate[0]*self.sim_obj.pop.count_quarantined()
                  + self.testing_rate[1]*self.sim_obj.pop.get_new_quarantined()
                  + self.testing_rate[2]*wait_list) # defines the number of tests going to be run
        if self.testing_baseline is None:
            self.testing_baseline = 0
        elif tests < self.testing_baseline and wait_list > 0:
            tests = self.testing_baseline
        return int(tests)

    def check_students(self, day):
        '''Method to update whether students are added to the simulation.
        
        This funciton evaluates whether students should be added based on 
        `studnet_day_trigger`.
        
        If the current day is greater than `student_day_trigger`, students
        will be added to the simulation.
        
        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.
            Used to evaluate whether the simulation has passed the day trigger.
            
        '''
        
        # Change the policy based on conditions
        if self.student_day_trigger is not None and day >= self.student_day_trigger:
            student_mandate = True
        else:
            student_mandate = False

        # Actually change the conditions
        self.student_mandate = student_mandate
        return student_mandate

    def get_students_mandate(self):
        '''Method to return the current student mandate.

        Returns
        -------
        self.student_mandate : bool
        '''
        return self.student_mandate
