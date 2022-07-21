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
    '''
    A class designed to host the actual monte-carlo simulation and to track the results.

    Holds all of the attributes outlined in the simulation_data section of the
    main.json configuration file, in addition to the ones listed below.

    Attributes
    ----------
    verbose : bool
        A variable indicating whether to print updates with simulation information while running.
    track_new_infected : :obj:`np.array` of int
        Holds the number of new infections for each day of the simulation.
    track_infected : :obj:`np.array` of int
        Holds the number of infected people for each day of the simulation.
    track_susceptible : :obj:`np.array` of int
        Holds the number of susceptible people for each day of the simulation.
    track_recovered : :obj:`np.array` of int
        Holds the number of recovered people for each day of the simulation.
    track_dead : :obj:`np.array` of int
        Holds the number of dead people for each day of the simulation.
    track_hospitalized : :obj:`np.array` of int
        Holds the number of hospitalized people for each day of the simulation.
    track_quarantined : :obj:`np.array` of int
        Holds the number of people currently in quarantine for each day of the simulation.
    track_new_quarantined : :obj:`np.array` of int
        Holds the number of newly quarantined people for each day of the simulation.
    track_tested : :obj:`np.array` of int
        Holds the total number of tested people, updated for each day of the simulation.
    track_new_tested : :obj:`np.array` of int
        Holds the number of people tested that day, for each day of the simulations.
    track_testing_wait_list : :obj:`np.array` of int
        Holds the number of people who are waiting to get tested that day, for each day of the simulations.
    track_inf_students : :obj:`np.array` of int
        Holds the number of infected students for each day of the simulations.
    track_masks : :obj:`np.array` of bool
        A binary array that tracks if masks were required for each day of the simulation.
    track_lockdown : :obj:`np.array` of bool
        A binary array that tracks if lockdown was implemented for each day of the simulation.
    track_testing : :obj:`np.array` of bool
        A binary array that tracks if testing was implemented for each day of the simulation.
    track_time : :obj:`np.array` of float
        An array to track the time taken to run each day of the simulation.
    has_run : bool
        A variable indicating if this object has run a simulaiton yet.
    '''

    def __init__(self, config_file, config_dir="", verbose=False):
        ''' __init__ method docstring.

        Parameters
        ----------
        config_file : str
            The path to the configuration file used by this simulation.
        config_dir : str
            Path to the directory that stores the configuration file. Not required if config_file
            is a complete path.
        verbose : bool
            A variable indicating whether to print updates with simulation information while running.
        '''

        self.config_dir = config_dir
        self.load_general_parameters(config_file)
        self.load_disease_parameters(self.disease_config_file)

        self.init_classes() # Have to initalize the classes after we have all of the parameters

        self.verbose = verbose # Whether or not to print daily simulation information.

        self.set_code_version() # Set the version of the code being used to run simulation.

        # Arrays to store the values during the simulation
        self.track_new_infected = np.zeros(self.nDays, dtype=int) # new infections
        self.track_infected = np.zeros(self.nDays, dtype=int) # currently infected
        self.track_susceptible = np.zeros(self.nDays, dtype=int) # never been exposed
        self.track_recovered = np.zeros(self.nDays, dtype=int) # total recovered
        self.track_dead = np.zeros(self.nDays, dtype=int) # total deaths
        self.track_hospitalized = np.zeros(self.nDays, dtype=int) # total hospitalizations
        self.track_ICU = np.zeros(self.nDays, dtype=int) # total ICU
        self.track_quarantined = np.zeros(self.nDays, dtype=int) # population currently in quarantine
        self.track_new_quarantined = np.zeros(self.nDays, dtype=int) # newly quarantined that day
        self.track_tested = np.zeros(self.nDays, dtype=int)       # total tested individuals
        self.track_new_tested = np.zeros(self.nDays, dtype=int)   # new tested per day
        self.track_testing_wait_list = np.zeros(self.nDays, dtype=int) # counts the number of people waiting for tests each day
        self.track_inf_students = np.zeros(self.nDays, dtype=int) # total infected students
        self.track_masks = np.zeros(self.nDays, dtype=bool) # tracks masking mandates
        self.track_lockdown = np.zeros(self.nDays, dtype=bool) # tracks lockdown mandates
        self.track_testing = np.zeros(self.nDays, dtype=bool) # tracks testing mandates
        self.track_time = np.zeros(self.nDays, dtype=float) # time elapsed (in seconds) since start of simulation
        self.track_R0 = np.zeros(self.nDays, dtype=float) # daily R0
        self.track_R_eff = np.zeros(self.nDays, dtype=float) # daily effective R0
        self.track_HIT = np.zeros(self.nDays, dtype=float) # daily herd immunity threshold
        self.track_vaccinated = np.zeros(self.nDays, dtype=int) # total vaccinated
        self.track_gamma = np.zeros(self.nDays, dtype=float) # daily gamma value
        self.track_beta = np.zeros(self.nDays, dtype=float) # daily beta value
        self.track_n_interactions = np.zeros(self.nDays, dtype=int) # Daily number of interactions

        self.has_run = False  # Indicates if the sim has run yet

    def load_general_parameters(self, data_file):
        ''' Method to load in attributes from the general configuration file.

        Parameters are loaded from the simulation_data section of the configuration file.
        All parameter names are the same as the dictionary keys in the file.

        Parameters
        ----------
        data_file : str
            Path to the general configuration file.
        '''

        if isinstance(data_file, str):
            with open(data_file, encoding='utf-8') as file:
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

        #### Load in the virus types tracking arrays ####
        self.virus_names = list(self.variant_codes.keys())
        self.track_virus_types = {virus_name:np.zeros(self.nDays, dtype=int) for virus_name in self.virus_names}


    def load_disease_parameters(self, filename):
        ''' Method to load in attributes from the disease configuration file.

        All parameters in the file are loaded into the object, and parameter names
        are taken from dictionary keys.

        Parameters
        ----------
        filename : str
            Path to the disease configuration file.
        '''

        # If path is absolute, use it.
        if Path(filename).is_absolute():
            with open(filename, encoding='utf-8') as file:
                self.disease_parameters = json.load(file)

        # Assume that the configuration filename is relative to path of main config.
        # If not set, assume relative to working directory.
        # Last attempt try relative to cv19 project directory.
        else:
            filepath = Path(self.config_dir, filename)
            try:
                with open(filepath, encoding='utf-8') as file:
                    self.disease_parameters = json.load(file)

                return

            except FileNotFoundError:
                warnings.warn((f"Unable to find file: {filepath} "
                               "assuming directory is relative to main config. "
                               "Attempting read relative to CV19ROOT directory."))

                filepath = Path(CV19ROOT, filename)
                with open(filepath, encoding='utf-8') as file:
                    self.disease_parameters = json.load(file)

    def init_classes(self):
        ''' Method that links the policy, population, and interaction sites class objects with
        the simulation class (serves as pointer variables).
        '''

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
            warnings.warn((f"Command '{' '.join(git_version_cmd)}' returned a non-zero "
                           f"exit code: {e.returncode}."))
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

                    if name and str(Path(name).parents[0]) == 'cv19':
                        dirty = True

            except subprocess.CalledProcessError as e:
                warnings.warn((f"Command '{' '.join(git_dirty_cmd)}' returned a non-zero "
                               f"exit code: {e.returncode}."))
                print(e.output)

            except OSError:
                warnings.warn("Could not set code version from git.")

            if dirty:
                self.code_id += '-dirty'

    def run(self, fail_on_rerun=True):
        ''' Method that runs the monte-carlo simulation.

        This is the main function in the simulation class that generates the tracking data. The
        fail_on_rerun parameter is added to make sure that data from previous runs is not overwritten
        by running the simulation again.

        Parameters
        ----------
        fail_on_rerun : bool
            Variable to indicate whether the code should return an error if same object is
            run multiple times.
        '''

        # Check whether the simulation has already been run.
        if fail_on_rerun:
            information = ("When running again, previous results will be overwritten. "
                           "It is probably best to create a new simulation object. "
                           "However, if this is desired, please explicitly set the "
                           "fail_on_rerun argument to False.")
            self.check_has_run(check=False, information=information, fail=True)

        if self.verbose:
            print(f"Simulation code version (from git): {self.code_id}\n")

        # Get current time for measuring elapsed time of simulation.
        beg_time = timer()

        # Initalize variables to flag state changes
        old_mask_mandate = self.policy.initial_mask_mandate
        old_lockdown_mandate = self.policy.initial_lockdown_mandate
        old_testing_mandate = self.policy.initial_testing_mandate
        old_student_mandate = self.policy.initial_student_mandate
        # Loop over the number of days
        for day in range(self.nDays):

            ############### UPDATE TRACKING ###############

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
            daily_variant_counts = self.pop.count_virus_types()
            for virus_name in self.virus_names:
                self.track_virus_types[virus_name][day] = daily_variant_counts[virus_name]

            self.track_vaccinated[day] = self.pop.count_vaccinated()

            self.new_tests = 0
            new_recovered = 0

            if day != 0:
                new_recovered = self.track_recovered[day] - self.track_recovered[day-1]
                new_dead = self.track_dead[day] - self.track_dead[day-1]
                self.track_new_infected[day] = self.track_infected[day]-self.track_infected[day-1]+new_recovered+new_dead
                self.track_new_tested[day] = self.track_tested[day] - self.track_tested[day-1]

                self.calculate_SIR_metrics(day)

            ############### UPDATE POLICY ###############
            mask_mandate = self.policy.update_mask_mandate(day=day)
            if mask_mandate != old_mask_mandate and self.verbose:
                print(f"Day: {day}, Mask Mandate: {mask_mandate}")
            old_mask_mandate = mask_mandate

            lockdown = self.policy.update_lockdown(day=day)
            if lockdown != old_lockdown_mandate and self.verbose:
                print(f"Day: {day}, Lockdown: {lockdown}")
            old_lockdown_mandate = lockdown

            testing_ON = self.policy.update_testing(day)
            if testing_ON != old_testing_mandate and self.verbose:
                print(f"Day: {day}, Testing: {testing_ON}")
            old_testing_mandate = testing_ON

            students_go = self.policy.check_students(day=day)
            if students_go != old_student_mandate and self.verbose:
                print(f"Day: {day}, Uni Mandate: {students_go}")
            old_student_mandate = students_go

            # Remove dead agents from site attendence
            self.inter_sites.remove_dead()

            #infect random students on the day they come in
            if self.inter_sites.students_on and day == self.policy.student_day_trigger:
                infStudents = np.random.randint(self.inf_students_lower, self.inf_students_upper)
                indices = np.random.choice(self.pop.get_student_indices(), infStudents, replace=False)
                # Convert virus type to virus code
                student_default_virus_code = self.variant_codes[self.student_default_virus_type]
                self.pop.infect_incoming_students(indices=indices, day=day, virus_type=student_default_virus_code)

            ############### UPDATE VISITORS ###############
            #add a random number of visitors to the population
            num_vis = np.random.choice(a=self.N_VIS_OPTION, p=self.N_VIS_PROB)
            visitors_ind = [x for x in range(self.nPop, self.nPop+num_vis-1)]
            vis_age = np.random.choice(a=self.pop.age_options, p=self.pop.age_weights, size=num_vis)
            for i in range(0, num_vis):
                visitor = Person(index=i+self.nPop, sim_obj=self, infected=True, recovered=False, dead=False,
                                 hospitalized=False, ICU=False, quarantined=False, quarantined_day=None, infected_day=None,
                                 recovered_day=None, death_day=None, others_infected=None,
                                 cure_days=None, recent_infections=None, vaccinated=False, age=vis_age[i],
                                 job=None,house_index=None, isolation_tendencies=0.2,
                                 case_severity='Mild', has_mask=True, virus_type="alpha")
                self.pop.population.append(visitor)

            ############### UPDATE INTERACTION SITES ###############
            will_visit_B = self.inter_sites.will_visit_site(self.inter_sites.get_grade_B_sites(), self.will_go_prob["B"])
            self.inter_sites.site_interaction(will_visit_B, day, personal=False, grade_code="B")
            if not lockdown:
                will_visit_A = self.inter_sites.will_visit_site(self.inter_sites.get_grade_A_sites(), self.will_go_prob["A"])
                self.inter_sites.site_interaction(will_visit_A, day, personal=True, grade_code="A")
                will_visit_C = self.inter_sites.will_visit_site(self.inter_sites.get_grade_C_sites(), self.will_go_prob["C"])
                self.inter_sites.site_interaction(will_visit_C, day, personal=False, grade_code="C")

            if self.inter_sites.students_on and students_go:
                will_visit_food = self.inter_sites.will_visit_site(self.inter_sites.get_food_sites(), self.will_go_prob["FOOD"])
                self.inter_sites.site_interaction(will_visit_food, day, personal=True, grade_code="FOOD")
                if not lockdown:
                    will_visit_lects = self.inter_sites.will_visit_site(self.inter_sites.get_lect_sites(),
                                                                        self.will_go_prob["LECT"])
                    self.inter_sites.site_interaction(will_visit_lects, day, personal=True, grade_code="LECT")
                    will_visit_study = self.inter_sites.will_visit_site(self.inter_sites.get_study_sites(),
                                                                        self.will_go_prob["STUDY"])
                    self.inter_sites.site_interaction(will_visit_study, day, personal=False, grade_code="STUDY")

            # Manage masks
            if mask_mandate:
                self.pop.change_mask_wearing()

            # Manage at home interactions
            self.inter_sites.house_interact(day)
            self.inter_sites.student_house_interact(day)
            # Residence interactions
            if self.inter_sites.students_on and students_go:
                will_visit_res = self.inter_sites.will_visit_site(self.inter_sites.get_res_sites(), self.will_go_prob["RES"])
                self.inter_sites.site_interaction(will_visit_res, day, personal=True, grade_code="RES")

            # Manage testing sites
            if testing_ON:
                tests = self.policy.get_num_tests(self.track_testing_wait_list[day])
                self.inter_sites.testing_site(tests, day)

            # Manage Quarantine
            self.pop.update_quarantine(day)

            # Manage Vaccines
            self.pop.update_vaccinated(day)
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
                print((f"Day: {day}, "
                       f"infected: {self.track_infected[day]}, "
                       f"recovered: {self.track_recovered[day]}, "
                       f"susceptible: {self.track_susceptible[day]}, "
                       f"dead: {self.track_dead[day]}, "
                       f"hospitalized: {self.track_hospitalized[day]}, "
                       f"ICU: {self.track_ICU[day]}, "
                       f"tested: {self.track_tested[day]}, "
                       f"total quarantined: {self.track_quarantined[day]}, "
                       f"infected students: {self.track_inf_students[day]}, "
                       f"vaccinated: {self.track_vaccinated[day]}"))

                # Print variants
                print("Variants", end=": ")
                for key, val in self.track_virus_types.items():
                    print(f"{key}:{val[day]}", end=", ")
                print("\n")

        if self.verbose:
            time_seconds = timer() - beg_time
            m, s = divmod(time_seconds, 60)
            h, m = divmod(m, 60)
            print(f"{'':-<80}")
            print("Simulation summary:")
            print(f"    Time elapsed: {h:02.0f}:{m:02.0f}:{s:02.0f}")
            print(f"    {self.track_susceptible[-1]} never got it")
            print(f"    {self.track_dead[-1]} died")
            print(f"    {np.max(self.track_infected)} had it at the peak")
            print(f"    {self.track_tested[day]} were tested")
            print(f"    {np.max(self.track_quarantined)} were in quarantine at the peak")
            print(f"    {np.max(self.track_hospitalized)} at peak hospitalizations")
            print(f"    {np.max(self.track_dead[-1])} at peak deaths")
            print("    The breakdown of the variants is", end=": ")
            for key, val in self.track_virus_types.items():
                print(f"{key}-{np.max(val)}", end=", ")
            print("")
            print(f"    {self.track_vaccinated[day]} people were vaccinated")
            print(f"    {self.track_vaccinated[day]/self.nPop*100:.2f}% of population was vaccinated.")

        self.has_run = True

    def calculate_SIR_metrics(self, day):
        '''Method to caclulate all metrics related to SIR models.

        These variables are defined in the wikipedia page and are calculated as such. No variables are
        returned, all values are set inside the function in the tracking arrays.

        Wikipedia page link: https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology

        The following variables are calculated: gamma, beta, R0, R effective, and HIT (herd immunity threshold).
        '''

        # Define variables in accordance with wikipedia page
        dR_dt = self.track_recovered[day] - self.track_recovered[day - 1]
        dI_dt = self.track_new_infected[day]
        S, I = self.track_susceptible[day], self.track_infected[day]
        N = self.parameters["simulation_data"]["nPop"]

        gamma = dR_dt / I if I > 0 else 0
        beta = (dI_dt + gamma*I)*(N/(I*S)) if I*S > 0 else 0

        if day - self.R0_lag_time >= 0:

            # Use the old gamma (infected rate) and current beta (recovery rate)
            lagged_gamma = self.track_gamma[day - self.R0_lag_time]
            daily_R0 = beta / lagged_gamma if lagged_gamma != 0 else 0
            daily_R_eff = daily_R0 * (S/N)
            HIT = 1 - 1/daily_R_eff if daily_R_eff != 0 else 1

            self.track_R0[day] = daily_R0
            self.track_R_eff[day] = daily_R_eff
            self.track_HIT[day] = HIT

        self.track_gamma[day], self.track_beta[day] = gamma, beta

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
             plot_tested=True, plot_quarantined=True, plot_new_tests=True, plot_new_quarantined=False, plot_masks=True,
             plot_hospitalized=True, plot_ICU=True, plot_lockdown=True, plot_testing=True, plot_students=True, plot_R0=False,
             plot_R_eff=False, plot_HIT=False, plot_gamma=False, plot_beta=False, plot_vaccinated=True, plot_virus_types=None,
             plot_n_interactions=False, log=False):

        ''' Method used to plot simulation results.

        Will return a warning or error if the simulation has not been run yet. For plotting the number of interactions,
        you must supply a list with the codes for the sites you wish to plot.

        Parameters
        ----------
        plot_* : bool
            Takes in a single variable for each tracking array held in the simulation class object. The
            variable is of name plot_<tracked value name>, for example plot_hospitalized. Setting this
            parameter to `True` will plot the array, and `False` will not. An exception to this is when
            plotting virus_types and n_interactions, which should be tuples or lists of the
            appropriate keys for those variables.
        log : bool
            Indicate whether to plot with a log scale on the y-axis.
        '''

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
        if plot_R0:
            plt.plot(days, self.track_R0, label="R0")
        if plot_R_eff:
            plt.plot(days, self.track_R_eff, label="Reff")
        if plot_HIT:
            plt.plot(days, self.track_HIT, label="HIT")
        if plot_gamma:
            plt.plot(days, self.track_gamma, label="gamma")
        if plot_beta:
            plt.plot(days, self.track_beta, label="beta")
        if plot_virus_types is not None:
            for key in plot_virus_types:
                if plot_virus_types[key]:
                    plt.plot(days, self.track_virus_types[key], label=str(key))
        if plot_n_interactions:
            for item in plot_n_interactions:
                if item in self.inter_sites.daily_interactions:
                    plt.plot(days, self.inter_sites.daily_interactions[item], label=f"Total Interactions: {item}")
        if plot_vaccinated:
            plt.plot(days, self.track_vaccinated, label='vaccinated')

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
        ''' Method to return all of the tracking arrays after the simulation has run.

        Returns
        -------
        returnDict : dict of `np.array`
            A dictionary holding all of the tracking arrays with the raw simulation results.
        '''

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
                      "time_elapsed":self.track_time, "R0":self.track_R0, "Reff":self.track_R_eff, "HIT":self.track_HIT,
                      "vaccinated":self.track_vaccinated, "gamma":self.track_gamma, "beta":self.track_beta}
        # Unpack the virus types
        for virus_type in self.track_virus_types.keys():
            returnDict[virus_type] = self.track_virus_types[virus_type]
        # Unpack the interaction site number of interactions
        for inter_site, inter_site_arr in self.inter_sites.daily_interactions.items():
            returnDict[f"total_daily_interactions_{inter_site}"] = inter_site_arr

        return returnDict
