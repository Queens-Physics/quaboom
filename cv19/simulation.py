import json
import warnings
import subprocess
from timeit import default_timer as timer
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from . import CV19ROOT
from .person import Person
from .population import Population
from .policy import Policy
from .interaction_sites import Interaction_Sites


class simulation():

    def __init__(self, config_file, config_dir="", verbose=False):

        self.config_dir = config_dir
        self.load_general_parameters(config_file)
        self.load_disease_parameters(self.disease_config_file)

        self.init_classes() # Have to initalize the classes after we have all of the parameters

        self.verbose = verbose # Whether or not to print daily simulation information.

        self.set_code_version() # Set the version of the code being used to run simulation.

        # Arrays to store the values during the simulation
        self.track_new_infected = np.zeros(self.nDays, dtype=int) # new infections
        self.track_infected = np.zeros(self.nDays, dtype=int)     # currently infected
        self.track_susceptible = np.zeros(self.nDays, dtype=int)  # never been exposed
        self.track_recovered = np.zeros(self.nDays, dtype=int)    # total recovered
        self.track_dead = np.zeros(self.nDays, dtype=int)         # total deaths
        self.track_hospitalized = np.zeros(self.nDays, dtype=int) # total hospitalizations
        self.track_ICU = np.zeros(self.nDays, dtype=int)          # total ICU
        self.track_quarantined = np.zeros(self.nDays, dtype=int)  # population currently in quarantine
        self.track_new_quarantined = np.zeros(self.nDays, dtype=int)
        self.track_tested = np.zeros(self.nDays, dtype=int)       # total tested individuals
        self.track_new_tested = np.zeros(self.nDays, dtype=int)   # new tested per day
        self.track_testing_wait_list = np.zeros(self.nDays, dtype=int) # counts the number of people waiting to get tests each day
        self.track_inf_students = np.zeros(self.nDays, dtype=int)

        self.track_masks = np.zeros(self.nDays, dtype=bool)
        self.track_lockdown = np.zeros(self.nDays, dtype=bool)
        self.track_testing = np.zeros(self.nDays, dtype=bool)

        self.track_time = np.zeros(self.nDays, dtype=float) # time elapsed (in seconds) since start of simulation

        self.has_run = False                                 # Indicates if the sim has run yet

    def load_general_parameters(self, data_file):
        if isinstance(data_file, str):
            with open(data_file) as file:
                self.parameters = json.load(file)

            self.config_dir = Path(data_file).parent

        elif isinstance(data_file, dict):
            self.parameters = data_file

        else:
            raise TypeError("Please supply dictionary object or file path.")

        #### Do the simulation parameters ####
        attributes = self.parameters["simulation_data"].keys()
        for attr in attributes:
            setattr(self, attr, self.parameters["simulation_data"][attr])

        #### Store the constant person parameters here so they are not duplicated ####
        person_attributes = self.parameters["person_data"].keys()
        for attr in person_attributes:
            setattr(self, attr, self.parameters["person_data"][attr])

    def load_disease_parameters(self, filename):
        # If path is absolute, use it.
        if Path(filename).is_absolute():
            with open(filename) as file:
                self.disease_parameters = json.load(file)

        # Assume that the configuration filename is relative to path of main config.
        # If not set, assume relative to working directory.
        # Last attempt try relative to cv19 project directory.
        else:
            filepath = Path(self.config_dir, filename)
            try:
                with open(filepath) as file:
                    self.disease_parameters = json.load(file)

                return

            except FileNotFoundError:
                warnings.warn(("Unable to find file: {} "
                               "assuming directory is relative to main config. "
                               "Attempting read relative to CV19ROOT directory.").format(filepath))

                filepath = Path(CV19ROOT, filename)
                with open(filepath) as file:
                    self.disease_parameters = json.load(file)

    def init_classes(self):
        # Initalize the policy class
        self.policy = Policy(self)

        # Initialize the population
        self.pop = Population(self)

        # Initalize the interaction sites
        self.inter_sites = Interaction_Sites(self)

    def set_code_version(self):
        '''Method to get and set the version of the code used to run the simulation.

        Note
        ----
        This function should really be using the --dirty flag, but only based
        on certain files. For example, local modifications to the notebook do not
        matter, whereas any modifications to the main classes could.
        '''
        # By default, set the code identifier to None.
        self.code_id = None

        # Describe the tag as best as possible.
        # Fall back to commit ID in the case of no existing tag.
        git_version_cmd = ['git', 'describe', '--always', '--tag', '--abbrev=12']

        try:
            self.code_id = subprocess.check_output(git_version_cmd, text=True)
            self.code_id = self.code_id.strip()

        except subprocess.CalledProcessError as e:
            warnings.warn(("Command '{}' returned a non-zero "
                           "exit code: {}.").format(' '.join(git_version_cmd),
                                                    e.returncode))
            print(e.output)

        except OSError:
            warnings.warn("Could not set code version from git.")

        if self.code_id is not None:
            # By default, assume no local modifications.
            dirty = False

            # Check for any differences.
            git_dirty_cmd = ['git', 'diff', '--name-status', 'HEAD']

            try:
                diff_names = subprocess.check_output(git_dirty_cmd, text=True)
                for line in diff_names.split('\n'):
                    # Need to check for any whitespace, if entire line is whitespace ignore.
                    name = line.split()[1] if line.strip() else ''

                    if name and name not in ['RunEpidemicPlot.ipynb']:
                        dirty = True

            except subprocess.CalledProcessError as e:
                warnings.warn(("Command '{}' returned a non-zero "
                               "exit code: {}.").format(' '.join(git_dirty_cmd),
                                                        e.returncode))
                print(e.output)

            except OSError:
                warnings.warn("Could not set code version from git.")

            if dirty:
                self.code_id += '-dirty'

    def run(self, fail_on_rerun=True):
        # Check whether the simulation has already been run.
        if fail_on_rerun:
            information = ("When running again, previous results will be overwritten. "
                           "It is probably best to create a new simulation object. "
                           "However, if this is desired, please explicitly set the "
                           "fail_on_rerun argument to False.")
            self.check_has_run(check=False, information=information, fail=True)

        # Get current time for measuring elapsed time of simulation.
        beg_time = timer()

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
            self.track_ICU[day] = self.pop.count_ICU()
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
            if mask_mandate != old_mask_mandate and self.verbose:
                print("Day: {}, Mask Mandate: {}".format(day, mask_mandate))
            old_mask_mandate = mask_mandate

            lockdown = self.policy.update_lockdown(day=day)
            if lockdown != old_lockdown_mandate and self.verbose:
                print("Day: {}, Lockdown: {}".format(day, lockdown))
            old_lockdown_mandate = lockdown

            testing_ON = self.policy.update_testing(day)
            if testing_ON != old_testing_mandate and self.verbose:
                print("Day: {}, Testing: {}".format(day, testing_ON))
            old_testing_mandate = testing_ON

            students_go = self.policy.check_students(day=day)
            if students_go != old_student_mandate and self.verbose:
                print("Day: {}, Uni Mandate: {}".format(day, students_go))
            old_student_mandate = students_go

            ############### VISITOR STUFF ###############
            #add a random number of visitors to the population
            num_vis = np.random.choice(a=self.N_VIS_OPTION, p=self.N_VIS_PROB)
            visitors_ind = [x for x in range(self.nPop, self.nPop+num_vis-1)]

            for i in range(0, num_vis):
                vis_age = np.random.randint(self.vis_age_lower, self.vis_age_upper)

                visitor = Person(index=i+self.nPop, sim_obj=self, infected=True, recovered=False, dead=False, hospitalized=False, ICU=False,
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
                        warnings.warn("Did not die correctly.", RuntimeWarning)

                else:
                    # Update cured stuff
                    is_cured = infected_person.check_cured(day)
                    if is_cured and not self.pop.update_cured(index=infected_person.get_index()):
                        warnings.warn("Did not cure correctly.", RuntimeWarning)

                    # Update quarintine stuff
                    infected_person.check_quarantine(day)

            self.track_time[day] = timer() - beg_time

            if self.verbose:
                print(("Day: {}, "
                       "infected: {}, "
                       "recovered: {}, "
                       "suceptible: {}, "
                       "dead: {}, "
                       "hospitalized: {}, "
                       "ICU: {}, "
                       "tested: {}, "
                       "total quarantined: {}, "
                       "infected students: {}").format(day,
                                                       self.track_infected[day],
                                                       self.track_recovered[day],
                                                       self.track_susceptible[day],
                                                       self.track_dead[day],
                                                       self.track_hospitalized[day],
                                                       self.track_ICU[day],
                                                       self.track_tested[day],
                                                       self.track_quarantined[day],
                                                       self.track_inf_students[day]))

        if self.verbose:
            print('{:-<80}'.format(''))
            time_seconds = timer() - beg_time
            m, s = divmod(time_seconds, 60)
            h, m = divmod(m, 60)
            print('Time elapsed: {:02d}:{:02d}:{:02d}'.format(int(h), int(m), int(s)))
            print("At the end,", self.track_susceptible[-1], "never got it")
            print(self.track_dead[-1], "died")
            print(np.max(self.track_infected), "had it at the peak")
            print(self.track_tested[day], "have been tested")
            print(np.max(self.track_quarantined), "were in quarantine at the peak")
            print(np.max(self.track_hospitalized), "at peak hospitalizations")
            print(np.max(self.track_dead[-1]), "at peak deaths")

        self.has_run = True

    def check_has_run(self, check, information="", fail=True):
        '''Method to check whether or not the simulation has run.

        Checks against the desired result.

        Parameters
        ----------
        check : bool
            The desired result (i.e., the simulation has or has not been run)
        information : str
            Any additional information to include in the warning or error message.
        fail : bool
            Whether or not to raise an exception upon an undesired result.

        Returns
        -------
        self.has_run : bool
            Whether or not the simulation has been run.
        '''
        if self.has_run == check:
            return self.has_run

        else:
            if not self.has_run:
                message = "Simulation has not been run."
            else:
                message = "Simulation has been run."

            if information:
                message += " " + information

            if fail:
                raise RuntimeError(message)
            else:
                warnings.warn(message, RuntimeWarning)

        return self.has_run

    def plot(self, plot_infected=True, plot_susceptible=True, plot_dead=True, plot_recovered=True, plot_new_infected=True,
             plot_tested=True, plot_quarantined=True, plot_new_tests=True, plot_new_quarantined=True, plot_masks=True,
             plot_hospitalized=False, plot_ICU=True, plot_lockdown=True, plot_testing=True, plot_students=True, log=False):

        self.check_has_run(check=True, information="Cannot make plots.", fail=True)

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
        if plot_hospitalized:
            plt.plot(days, self.track_hospitalized, label='hospitalized')
        if plot_ICU:
            plt.plot(days, self.track_ICU, label='ICU')
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
        self.check_has_run(check=True,
                           information="Cannot return zero-initialized arrays.",
                           fail=True)

        returnDict = {"infected":self.track_infected, "new_infected":self.track_new_infected,
                      "recovered":self.track_recovered, "susceptible":self.track_susceptible,
                      "dead":self.track_dead, "quarantined":self.track_quarantined,
                      "inf_students":self.track_inf_students, "total_tested":self.track_tested,
                      "new_tested":self.track_new_tested, "hospitalized":self.track_hospitalized,
                      "ICU":self.track_ICU, "testing_enforced":self.track_testing, 
                      "masks_enforced":self.track_masks, "lockdown_enforced":self.track_lockdown,
                      "time_elapsed":self.track_time}

        return returnDict
