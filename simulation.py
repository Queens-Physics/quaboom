import numpy as np
import matplotlib.pyplot as plt
import copy as copy

import Person
import Population
import Interaction_Sites
import Policy

#### LOAD IN PARAMS FROM CONFIG FILE ####
import config_files.config as config
# will_go_to_site parameters (prob person will go somewhere each day) 
A_WILL_GO_PROB = config.A_WILL_GO_PROB
B_WILL_GO_PROB = config.B_WILL_GO_PROB
C_WILL_GO_PROB = config.C_WILL_GO_PROB

# Testing parameters
TESTING_RATE = config.TESTING_RATE #rate at which people get positive tests (testing rate/infected person)

# Polciy variables
initial_mask_mandate = config.initial_mask_mandate
initial_lockdown_mandate = config.initial_lockdown_mandate
initial_testing = config.initial_testing
lockdown_trigger, lockdown_day_trigger = config.lockdown_trigger, config.lockdown_day_trigger
mask_trigger, mask_day_trigger = config.mask_trigger, config.mask_day_trigger
testing_trigger, testing_day_trigger = config.testing_trigger, config.testing_day_trigger

#### DEFINE THE CLASS ####

class simulation():
    
    def __init__(self, nPop, n0, nDays):
        
        self.nPop = nPop
        self.n0 = n0
        self.nDays = nDays

        # Initalize the policy class
        self.policy = Policy.Policy(initial_mask_mandate=initial_mask_mandate, initial_lockdown_mandate=initial_lockdown_mandate, 
                                   mask_trigger=mask_trigger, mask_day_trigger=mask_day_trigger, 
                                   lockdown_trigger=lockdown_trigger, lockdown_day_trigger=lockdown_day_trigger,
                                   testing_rate=TESTING_RATE, testing_trigger=testing_trigger, 
                                   testing_day_trigger=testing_day_trigger, 
                                   initial_testing=initial_testing)

        # Initialize the population
        self.pop = Population.Population(nPop, n0, policy=self.policy)

        # Initalize the interaction sites
        self.inter_sites = Interaction_Sites.Interaction_Sites(pop_obj=self.pop)

        # Link the pop and inter_sites to the policy class
        self.policy.set_simulation(population=self.pop, interaction_sites=self.inter_sites)

        # Arrays to store the values during the simulation                   
        self.track_new_infected = np.zeros(nDays, dtype=int) # new infections 
        self.track_infected = np.zeros(nDays, dtype=int)     # currently infected 
        self.track_susceptible = np.zeros(nDays, dtype=int)  # never been exposed
        self.track_recovered = np.zeros(nDays, dtype=int)    # total recovered
        self.track_dead = np.zeros(nDays, dtype=int)         # total deaths
        self.track_tested = np.zeros(nDays, dtype=int)       # total tested individuals
        self.track_quarantined = np.zeros(nDays, dtype=int)  # population currently in quarantine ACTUALLY DOES TOTAL QUARINTIED 
        self.track_testing_wait_list = np.zeros(nDays, dtype=int) # counts the number of people waiting to get tests each day
        self.track_masks = np.zeros(nDays, dtype=bool)
        self.track_lockdown = np.zeros(nDays, dtype=bool)
        self.track_testing = np.zeros(nDays, dtype=bool)
        
        self.has_run = False                                 # Indicates if the sim has run yet
        
        
    def run(self):
        
        # Initalize variables to flag state changes
        old_mask_mandate, old_lockdown, old_testing = initial_mask_mandate, initial_lockdown_mandate, initial_testing
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
            self.track_lockdown[day] = old_lockdown
            self.track_testing[day] = old_testing

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
            if lockdown != old_lockdown:
                print("Day: {}, Lockdown: {}".format(day, lockdown))
            old_lockdown = lockdown

            testing_ON = self.policy.update_testing(day)   
            if testing_ON != old_testing: 
                print("Day: {}, Testing: {}".format(day, testing_ON))
            old_testing = testing_ON

            ############### INTERACTION SITES STUFF ###############
            will_visit_A = self.inter_sites.will_visit_site(self.inter_sites.get_grade_A_sites(), A_WILL_GO_PROB)
            self.inter_sites.site_interaction(will_visit_A, day)
            if not lockdown:
                will_visit_B = self.inter_sites.will_visit_site(self.inter_sites.get_grade_B_sites(), B_WILL_GO_PROB)
                self.inter_sites.site_interaction(will_visit_B, day)
                will_visit_C = self.inter_sites.will_visit_site(self.inter_sites.get_grade_C_sites(), C_WILL_GO_PROB)
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
