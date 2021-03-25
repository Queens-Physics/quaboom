import numpy as np
import matplotlib.pyplot as plt
import copy as copy
import json
import random

import Person
import Population
import Interaction_Sites
import Policy

class simulation():
    
    def __init__(self, config_file):
        
        self.load_parameters(config_file)
        self.init_classes() # Have to initalize the classes after we have all of the parameters

        # Arrays to store the values during the simulation                   
        self.track_new_infected = np.zeros(self.nDays, dtype=int) # new infections 
        self.track_infected = np.zeros(self.nDays, dtype=int)     # currently infected 
        self.track_susceptible = np.zeros(self.nDays, dtype=int)  # never been exposed
        self.track_recovered = np.zeros(self.nDays, dtype=int)    # total recovered
        self.track_dead = np.zeros(self.nDays, dtype=int)         # total deaths
        self.track_tested = np.zeros(self.nDays, dtype=int)       # total tested individuals
        self.track_quarantined = np.zeros(self.nDays, dtype=int)  # population currently in quarantine 
        self.track_testing_wait_list = np.zeros(self.nDays, dtype=int) # counts the number of people waiting to get tests each day
        self.track_masks = np.zeros(self.nDays, dtype=bool)
        self.track_lockdown = np.zeros(self.nDays, dtype=bool)
        self.track_testing = np.zeros(self.nDays, dtype=bool)
        
        self.has_run = False                                 # Indicates if the sim has run yet
 
        
    def load_parameters(self, filename):
        file = open(filename)
        parameters = json.load(file)
        
        #### Do the simulation parameters ####
        sim_params = parameters["simulation_data"]
        self.nDays = sim_params["nDays"]
        self.nPop = sim_params["nPop"]
        self.n0 = sim_params["n0"]
        self.A_will_go_prob = sim_params["A_will_go_prob"]
        self.B_will_go_prob = sim_params["B_will_go_prob"]
        self.C_will_go_prob = sim_params["C_will_go_prob"]
        
        #### Do the policy parameters ####
        policy_params = parameters["policy_data"]
        self.testing_rate = policy_params["testing_rate"]
        self.initial_mask_mandate = policy_params["initial_mask_mandate"]
        self.mask_trigger = policy_params["mask_trigger"]
        self.mask_day_trigger = policy_params["mask_day_trigger"]
        self.initial_lockdown_mandate = policy_params["initial_lockdown_mandate"]
        self.lockdown_trigger = policy_params["lockdown_trigger"]
        self.lockdown_day_trigger = policy_params["lockdown_day_trigger"]
        self.initial_testing_mandate = policy_params["initial_testing_mandate"]
        self.testing_trigger = policy_params["testing_trigger"]
        self.testing_day_trigger = policy_params["testing_day_trigger"]
        self.testing_baseline = policy_params["testing_baseline"]
        
        #### Do the population parameters ####
        pop_params = parameters["population_data"]
        self.demographics_file = pop_params["demographics_file"]
        self.prob_has_mask = pop_params["prob_has_mask"]
        self.prob_of_test = pop_params["prob_of_test"]
        
        #### Do the interaction site parameters ####
        is_params = parameters["interaction_sites_data"]
        self.grade_per_pop = is_params["grade_per_pop"]
        self.grade_loyalty_means = is_params["grade_loyalty_means"]
        self.grade_loyalty_stds = is_params["grade_loyalty_stds"]
        self.base_infection_spread_prob = is_params["base_infection_spread_prob"]
        self.house_infection_spread_factor = is_params["house_infection_spread_factor"]
        self.quarantine_isolation_factor = is_params["quarantine_isolation_factor"]
        
        #### Do the person parameters ####
        person_params = parameters["person_data"]
        self.quarantine_time = person_params['quarantine_time']
        self.surgical_inward_eff = person_params['surgical_inward_eff']
        self.surgical_outward_eff = person_params['surgical_outward_eff']
        self.nonsurgical_inward_eff = person_params['nonsurgical_inward_eff']
        self.nonsurgical_outward_eff = person_params['nonsurgical_outward_eff']
        self.wear_mask_properly = person_params["wear_mask_properly"]
        self.mild_symptom_prob = person_params["mild_symptom_prob"]
        self.min_day_before_symptoms = person_params["min_day_before_symptoms"]
        self.max_day_before_symptoms = person_params["max_day_before_symptoms"]
        self.min_severe_days = person_params["min_severe_days"]
        self.max_severe_days = person_params["max_severe_days"]
        self.min_mild_days = person_params["min_mild_days"]
        self.max_mild_days = person_params["max_mild_days"]
        self.min_ICU_days = person_params["min_ICU_days"]
        self.max_ICU_days = person_params["max_ICU_days"]
        self.min_die_days = person_params["min_die_days"]
        self.max_die_days = person_params["max_die_days"]
        
    def init_classes(self):
        # Initalize the policy class
        self.policy = Policy.Policy(self)

        # Initialize the population
        self.pop = Population.Population(self)

        # Initalize the interaction sites
        self.inter_sites = Interaction_Sites.Interaction_Sites(self)
        
        
    def run(self):
        
        # Initalize variables to flag state changes
        old_mask_mandate = self.initial_mask_mandate
        old_lockdown_mandate = self.initial_lockdown_mandate
        old_testing_mandate = self.initial_testing_mandate
        # Loop over the number of days
        for day in range(self.nDays):

            ############### TRACKING STUFF ###############

            #Count all the different states of people
            self.track_infected[day] = self.pop.count_infected()
            self.track_susceptible[day] = self.pop.count_susceptible()
            self.track_recovered[day] = self.pop.count_recovered()
            self.track_dead[day] = self.pop.count_dead()
            self.track_tested[day] = self.pop.count_tested()
            self.track_quarantined[day] = self.pop.count_quarantined()
            self.track_testing_wait_list[day] = self.pop.get_testing_wait_list()
            
            self.track_masks[day] = old_mask_mandate
            self.track_lockdown[day] = old_lockdown_mandate
            self.track_testing[day] = old_testing_mandate

            self.new_tests = 0

            if day != 0:
                new_recovered = self.track_recovered[day] - self.track_recovered[day-1]
                new_dead = self.track_dead[day] - self.track_dead[day-1]
                self.track_new_infected[day] = self.track_infected[day]-self.track_infected[day-1]+new_recovered+new_dead

            ############### POLICY STUFF ###############
            mask_mandate = self.policy.update_mask_mandate(day=day)
            if mask_mandate != old_mask_mandate:
                print("Day: {}, Mask Mandate: {}".format(day, mask_mandate))
            old_mask_mandate = mask_mandate

            lockdown = self.policy.update_lockdown(day=day)
            if lockdown != old_lockdown_mandate:
                print("Day: {}, Lockdown: {}".format(day, lockdown))
            old_lockdown_mandate = lockdown

            testing_ON = self.policy.update_testing(day)   
            if testing_ON != old_testing_mandate: 
                print("Day: {}, Testing: {}".format(day, testing_ON))
            old_testing_mandate = testing_ON

            ############### INTERACTION SITES STUFF ###############
            will_visit_A = self.inter_sites.will_visit_site(self.inter_sites.get_grade_A_sites(), self.A_will_go_prob)
            self.inter_sites.site_interaction(will_visit_A, day)
            if not lockdown:
                will_visit_B = self.inter_sites.will_visit_site(self.inter_sites.get_grade_B_sites(), self.B_will_go_prob)
                self.inter_sites.site_interaction(will_visit_B, day)
                will_visit_C = self.inter_sites.will_visit_site(self.inter_sites.get_grade_C_sites(), self.C_will_go_prob)
                self.inter_sites.site_interaction(will_visit_C, day)

            # Manage at home interactions
            self.inter_sites.house_interact(day)

            # Manage testing sites        
            if (testing_ON): 
                tests = self.policy.get_num_tests(self.track_testing_wait_list[day])
                self.inter_sites.testing_site(tests, day)

            # Manage Quarantine
            self.pop.update_quarantine(day)

            ############### UPDATE POPULATION ###############
            for index in self.pop.get_infected(): 
                infected_person = self.pop.get_person(index=index) 

                if infected_person.get_case_severity() == "Death":
                    is_dead = infected_person.check_dead(day)
                    if is_dead and self.pop.update_dead(index=infected_person.get_index()) == False:
                        print("Did not die correctly")

                else:     
                    # Update cured stuff
                    is_cured = infected_person.check_cured(day)
                    if is_cured and self.pop.update_cured(index=infected_person.get_index()) == False:
                        print("Did not cure correctly")

                    # Update quarintine stuff
                    is_quarantined = infected_person.check_quarantine(day)

            print("Day: {}, infected: {}, recovered: {}, suceptible: {}, dead: {}, tested: {} total quarantined: {}".format(day, 
                                                                                          self.track_infected[day],
                                                                                          self.track_recovered[day],
                                                                                          self.track_susceptible[day],
                                                                                          self.track_dead[day],
                                                                                          self.track_tested[day],
                                                                                          self.track_quarantined[day]))
        print("At the end, ", self.track_susceptible[-1], "never got it")
        print(self.track_dead[-1], "died")
        print(np.max(self.track_infected), "had it at the peak")
        print(self.track_tested[day], "have been tested")
        print (np.max(self.track_quarantined), "were in quarantine at the peak")

        self.has_run = True
        
    def check_has_run(self):
        # Check that the sim has run
        if self.has_run==False:
            print("Simulation has not run yet, returning empty arrays")

    def plot(self, plot_infected=True, plot_susceptible=True, plot_dead=True, plot_recovered=True, plot_new_infected=True, 
             plot_tested=True, plot_quarantined=True, plot_masks=True, plot_lockdown=True, plot_testing=True, log=False):
        self.check_has_run()

        fig, ax = plt.subplots(figsize=(10,8), dpi=100)
        days = np.linspace(0,self.nDays, self.nDays, dtype=int)
        
        if plot_infected: plt.plot(days, self.track_infected, label='infected')
        if plot_susceptible: plt.plot(days, self.track_susceptible, label='susceptible')
        if plot_recovered: plt.plot(days, self.track_recovered, label='recovered')
        if plot_dead: plt.plot(days, self.track_dead, label='dead')
        if plot_new_infected: plt.plot(days, self.track_new_infected, label='new infections')
        if plot_quarantined: plt.plot(days, self.track_quarantined, label='quarantined')
        if plot_tested: plt.plot(days, self.track_tested, label='total tests')
            
        # Indicate when certain mandates were in place
        if plot_masks: 
            plt.fill_between(days, 0, 1, where=self.track_masks, alpha=0.3, 
                             transform=ax.get_xaxis_transform(), label="masks required")
        if plot_testing: 
            plt.fill_between(days, 0, 1, where=self.track_testing, alpha=0.3, 
                             transform=ax.get_xaxis_transform(), label="testing performed")
        if plot_lockdown: 
            plt.fill_between(days, 0, 1, where=self.track_lockdown, alpha=0.3, 
                             transform=ax.get_xaxis_transform(), label="lockdown implemented")

        plt.grid()
        plt.legend()
        if log: plt.yscale("log")
        plt.ylabel("People")
        plt.xlabel("Days")

    def get_arrays(self):
        self.check_has_run()

        return (self.track_infected, self.track_new_infected, self.track_recovered, self.track_susceptible, self.track_dead, 
                self.track_tested, self.track_quarantined, self.track_masks, self.track_lockdown)
