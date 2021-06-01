import json

import numpy as np
import matplotlib.pyplot as plt

from Person import Person
from Population import Population
from Policy import Policy
from Interaction_Sites import Interaction_Sites


class simulation():

    def __init__(self, config_file):

        self.load_general_parameters(config_file)
        self.load_disease_parameters(self.disease_config_file)

        self.init_classes() # Have to initalize the classes after we have all of the parameters

        # Arrays to store the values during the simulation
        self.track_new_infected = np.zeros(self.nDays, dtype=int) # new infections
        self.track_infected = np.zeros(self.nDays, dtype=int)     # currently infected
        self.track_susceptible = np.zeros(self.nDays, dtype=int)  # never been exposed
        self.track_recovered = np.zeros(self.nDays, dtype=int)    # total recovered
        self.track_dead = np.zeros(self.nDays, dtype=int)         # total deaths
        self.track_hospitalized = np.zeros(self.nDays, dtype=int) # total hospitalizations
        self.track_quarantined = np.zeros(self.nDays, dtype=int)  # population currently in quarantine
        self.track_new_quarantined = np.zeros(self.nDays, dtype=int)
        self.track_tested = np.zeros(self.nDays, dtype=int)       # total tested individuals
        self.track_new_tested = np.zeros(self.nDays, dtype=int)   # new tested per day
        self.track_testing_wait_list = np.zeros(self.nDays, dtype=int) # counts the number of people waiting to get tests each day
        self.track_inf_students = np.zeros(self.nDays, dtype=int)

        self.track_masks = np.zeros(self.nDays, dtype=bool)
        self.track_lockdown = np.zeros(self.nDays, dtype=bool)
        self.track_testing = np.zeros(self.nDays, dtype=bool)

        self.has_run = False                                 # Indicates if the sim has run yet

    def load_general_parameters(self, data_file):
        if type(data_file)==str:
            with open(data_file) as file:
                self.parameters = json.load(file)
        elif type(data_file)==dict:
            self.parameters = data_file
        else:
            print("Error: Please supply dictionary object or file path.")
            return 

        #### Do the simulation parameters ####
        attributes = self.parameters["simulation_data"].keys()
        for attr in attributes:
            setattr(self, attr, self.parameters["simulation_data"][attr])

        #### Store the constant person parameters here so they are not duplicated ####
        person_attributes = self.parameters["person_data"].keys()
        for attr in person_attributes:
            setattr(self, attr, self.parameters["person_data"][attr])

    def load_disease_parameters(self, filename):
        with open(filename) as file:
            self.disease_parameters = json.load(file)

    def init_classes(self):
        # Initalize the policy class
        self.policy = Policy(self)

        # Initialize the population
        self.pop = Population(self)

        # Initalize the interaction sites
        self.inter_sites = Interaction_Sites(self)

    def run(self):

        # Initalize variables to flag state changes
        old_mask_mandate = self.policy.initial_mask_mandate
        old_lockdown_mandate = self.policy.initial_lockdown_mandate
        old_testing_mandate = self.policy.initial_testing_mandate
        old_student_mandate = self.policy.initial_student_mandate
        # Loop over the number of days
        for day in range(self.nDays):

            ############### TRACKING STUFF ###############

            #Count all the different states of people
            self.track_infected[day] = self.pop.count_infected()
            self.track_susceptible[day] = self.pop.count_susceptible()
            self.track_recovered[day] = self.pop.count_recovered()
            self.track_dead[day] = self.pop.count_dead()
            self.track_hospitalized[day] = self.pop.count_hospitalized()
            self.track_tested[day] = self.pop.count_tested()
            self.track_quarantined[day] = self.pop.count_quarantined()
            self.track_testing_wait_list[day] = self.pop.get_testing_wait_list()

            self.track_masks[day] = old_mask_mandate
            self.track_lockdown[day] = old_lockdown_mandate
            self.track_testing[day] = old_testing_mandate

            self.track_new_quarantined[day] = self.pop.get_new_quarantined()
            self.track_inf_students[day] = self.pop.count_infected_students()

            self.new_tests = 0

            if day != 0:
                new_recovered = self.track_recovered[day] - self.track_recovered[day-1]
                new_dead = self.track_dead[day] - self.track_dead[day-1]
                self.track_new_infected[day] = self.track_infected[day]-self.track_infected[day-1]+new_recovered+new_dead
                self.track_new_tested[day] = self.track_tested[day] - self.track_tested[day-1]

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

            students_go = self.policy.check_students(day=day)
            if students_go != old_student_mandate:
                print("Day: {}, Uni Mandate: {}".format(day, students_go))
            old_student_mandate = students_go

            ############### VISITOR STUFF ###############
            #add a random number of visitors to the population
            num_vis = np.random.choice(a=self.N_VIS_OPTION, p=self.N_VIS_PROB)
            visitors_ind = [x for x in range(self.nPop, self.nPop+num_vis-1)]

            for i in range(0, num_vis):
                vis_age = np.random.randint(self.vis_age_lower, self.vis_age_upper)

                visitor = Person(index=i+self.nPop, sim_obj=self, infected=True, recovered=False, dead=False,
                                 quarantined=False, quarantined_day=None, infected_day=None, recovered_day=None,
                                 death_day=None, others_infected=None, cure_days=None, recent_infections=None,
                                 age=vis_age, job=None,house_index=None, isolation_tendencies=0.2, case_severity='Mild',
                                 has_mask=True)
                self.pop.population.append(visitor)

            ############### INTERACTION SITES STUFF ###############
            will_visit_A = self.inter_sites.will_visit_site(self.inter_sites.get_grade_A_sites(), self.will_go_prob["A"])
            self.inter_sites.site_interaction(will_visit_A, day)
            if not lockdown:
                will_visit_B = self.inter_sites.will_visit_site(self.inter_sites.get_grade_B_sites(), self.will_go_prob["B"])
                self.inter_sites.site_interaction(will_visit_B, day)
                will_visit_C = self.inter_sites.will_visit_site(self.inter_sites.get_grade_C_sites(), self.will_go_prob["C"])
                self.inter_sites.site_interaction(will_visit_C, day)
            if students_go:
                will_visit_study = self.inter_sites.will_visit_site(self.inter_sites.get_study_sites(),
                                                                    self.will_go_prob["STUDY"])
                self.inter_sites.site_interaction(will_visit_study, day)
                will_visit_food = self.inter_sites.will_visit_site(self.inter_sites.get_food_sites(),
                                                                   self.will_go_prob["FOOD"])
                self.inter_sites.site_interaction(will_visit_food, day)
                if not lockdown:
                    will_visit_lects = self.inter_sites.will_visit_site(self.inter_sites.get_lect_sites(),
                                                                        self.will_go_prob["LECT"])
                    self.inter_sites.site_interaction(will_visit_lects, day)

            # Manage at home interactions
            self.inter_sites.house_interact(day)

            # Manage testing sites
            if testing_ON:
                tests = self.policy.get_num_tests(self.track_testing_wait_list[day])
                self.inter_sites.testing_site(tests, day)

            # Manage Quarantine
            self.pop.update_quarantine(day)

            ############### UPDATE POPULATION ###############
            # remove the guest visitors
            self.pop.remove_visitors(visitors_ind)
            for index in self.pop.get_infected():
                infected_person = self.pop.get_person(index=index)

                if infected_person.get_case_severity() == "Death":
                    is_dead = infected_person.check_dead(day)
                    if is_dead and not self.pop.update_dead(index=infected_person.get_index()):
                        print("Did not die correctly")

                else:
                    # Update cured stuff
                    is_cured = infected_person.check_cured(day)
                    if is_cured and not self.pop.update_cured(index=infected_person.get_index()):
                        print("Did not cure correctly")

                    # Update quarintine stuff
                    infected_person.check_quarantine(day)

            print("Day: {}, infected: {}, recovered: {}, suceptible: {}, dead: {}, hospitalized: {}, tested: {}, total quarantined: {}, infected students: {}".format(day,
                                                                                      self.track_infected[day],
                                                                                      self.track_recovered[day],
                                                                                      self.track_susceptible[day],
                                                                                      self.track_dead[day],
                                                                                      self.track_hospitalized[day],
                                                                                      self.track_tested[day],
                                                                                      self.track_quarantined[day],
                                                                                      self.track_inf_students[day]))
        print("At the end, ", self.track_susceptible[-1], "never got it")
        print(self.track_dead[-1], "died")
        print(np.max(self.track_infected), "had it at the peak")
        print(self.track_tested[day], "have been tested")
        print(np.max(self.track_quarantined), "were in quarantine at the peak")
        print(np.max(self.track_hospitalized), "at peak hospitalizations")
        print(np.max(self.track_dead[-1]), "at peak deaths")

        self.has_run = True

    def check_has_run(self):
        # Check that the sim has run
        if not self.has_run:
            print("Simulation has not run yet, returning empty arrays")

    def plot(self, plot_infected=True, plot_susceptible=True, plot_dead=True, plot_recovered=True, plot_new_infected=True,
             plot_tested=True, plot_quarantined=True, plot_new_tests=True, plot_new_quarantined=True, plot_masks=True, plot_lockdown=True, plot_testing=True,
             plot_students=True, log=False):
        
        self.check_has_run()

        _, ax = plt.subplots(figsize=(10,8), dpi=100)
        days = np.linspace(0,self.nDays, self.nDays, dtype=int)

        # Plot the tracking arrays
        if plot_infected:
            plt.plot(days, self.track_infected, label='infected')
        if plot_susceptible:
            plt.plot(days, self.track_susceptible, label='susceptible')
        if plot_recovered:
            plt.plot(days, self.track_recovered, label='recovered')
        if plot_dead:
            plt.plot(days, self.track_dead, label='dead')
        if plot_new_infected:
            plt.plot(days, self.track_new_infected, label='new infections')
        if plot_quarantined:
            plt.plot(days, self.track_quarantined, label='quarantined')
        if plot_tested:
            plt.plot(days, self.track_tested, label='total tests')
        if plot_new_tests:
            plt.plot(days, self.track_new_tested, label='new tests')
        if plot_new_quarantined:
            plt.plot(days, self.track_new_quarantined, label='new quarantined')
        if plot_students:
            plt.plot(days, self.track_inf_students, label="infected students")

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

        # Final graph formatting
        plt.grid()
        plt.legend()
        if log:
            plt.yscale("log")
        plt.ylabel("People")
        plt.xlabel("Days")

    def get_arrays(self):
        self.check_has_run()
        returnDict = {"infected":self.track_infected, "new_infected":self.track_new_infected, "recovered":self.track_recovered, 
                      "susceptible":self.track_susceptible, "dead":self.track_dead, "quarantined":self.track_quarantined, 
                      "inf_students":self.track_inf_students, "tested":self.track_tested, "new_tested":self.track_new_tested,
                      "testing_enforced":self.track_tested, "masks_enforced":self.track_masks,
                      "lockdown_enforced":self.track_lockdown}
        return returnDict
