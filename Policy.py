class Policy:
    '''
    Handles all of the metrics that would be dealt with by policy, including mask mandates, quarantines, testing, 
    and travel/lockdowns. 
    Initalized once for the entire simulation. 
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
        return self.mask_mandate
    
    
    def update_lockdown(self, day):
        
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
        return self.lockdown_mandate
    
    def update_testing(self,day):
        if self.testing_day_trigger is not None and day >= self.testing_day_trigger: 
            testing = True
        elif self.testing_trigger is not None and self.sim_obj.pop.count_quarantined()/self.prob_of_symptoms/self.sim_obj.pop.nPop > self.testing_trigger: 
            testing = True
        else:
            testing = False
        return testing
    
    def get_num_tests(self,wait_list):
    # The number of tests is assumed to have a linaear realtionship with the number of quarantined people, the number of people who have just joined the quarantine and the waitlist 
    # testing_rate = [number of tests/people in quarantine, number of tests/people newly in quarantine, number of tests/number of people in the waitlist]
        tests =  (self.testing_rate[1]*self.sim_obj.pop.count_quarantined()
                  + self.testing_rate[2]*self.sim_obj.pop.get_new_quarantined()
                  + self.testing_rate[3]*wait_list) # defines the number of tests going to be run
        if self.testing_baseline is None: 
            self.testing_baseline = 0
        elif tests < self.testing_baseline and wait_list > 0: 
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
