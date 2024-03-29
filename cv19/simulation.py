import warnings
import subprocess
from timeit import default_timer as timer
from pathlib import Path
import tomli

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from . import CV19ROOT
from .population import Population
from .policy import Policy
from .interaction_sites import InteractionSites


class Simulation():
    """
    A class designed to host the actual monte-carlo simulation and to track the results.

    Holds all of the attributes outlined in the simulation_data section of the
    main.toml configuration file, in addition to the ones listed below.

    Attributes
    ----------
    verbose : bool
        A variable indicating whether to print updates with simulation information while running.
    tracking_df : pd.DataFrame
        A pandas DataFrame object that stores all the tracking arrays for a given simulation. Each
        array is of length nDays.
    virus_names : list of str
        A list of identifying codes for each virus type that could be in the simulation.
    track_virus_types : dict of np.array
        A dictionary containing the number of agents infected with each virus type in the simulation.
    has_run : bool
        A variable indicating if this object has run a simulaiton yet.
    """

    def __init__(self, config_file, config_dir="", config_override_data=None, verbose=False):
        """ __init__ method docstring.

        Parameters
        ----------
        config_file : str
            The path to the configuration file used by this simulation.
        config_dir : str
            Path to the directory that stores the configuration file. Not required if config_file
            is a complete path.
        config_override_data : dict
            A dictionary of configuration file instances that can be used to override the files
            specified in the main configuration file. Designed to allow tabular mode to edit parameters
            in configuration files other than main.
        verbose : bool
            A variable indicating whether to print updates with simulation information while running.
        """

        self.config_dir = config_dir
        self.load_general_parameters(config_file)
        self.load_disease_parameters(self.disease_config_file, config_override_data)

        self.init_classes()  # Have to initalize the classes after we have all of the parameters

        self.verbose = verbose  # Whether or not to print daily simulation information.

        self.set_code_version()  # Set the version of the code being used to run simulation.

        self.make_tracking_df()

        # Check that input parameters are valid
        assert self.nPop >= self.num_students
        assert self.nPop >= sum(self.variants.values())

        self.has_run = False  # Indicates if the sim has run yet

    def load_general_parameters(self, data_file):
        """ Method to load in attributes from the general configuration file.

        Parameters are loaded from the simulation_data section of the configuration file.
        All parameter names are the same as the dictionary keys in the file.

        Parameters
        ----------
        data_file : str
            Path to the general configuration file.
        """

        if isinstance(data_file, str):
            with open(data_file, 'rb') as file:
                self.parameters = tomli.load(file)

            self.config_dir = Path(data_file).parent

        elif isinstance(data_file, dict):
            self.parameters = data_file

        else:
            raise TypeError("Please supply dictionary object or file path.")

        # Do the simulation parameters
        attributes = self.parameters["simulation_data"].keys()
        for attr in attributes:
            setattr(self, attr, self.parameters["simulation_data"][attr])

        # Store the constant person parameters here so they are not duplicated
        person_attributes = self.parameters["person_data"].keys()
        for attr in person_attributes:
            setattr(self, attr, self.parameters["person_data"][attr])

        # Load in the virus types tracking arrays
        self.virus_names = list(self.variant_codes.keys())
        self.track_virus_types = {virus_name: np.zeros(self.nDays, dtype=int) for virus_name in self.virus_names}

    def load_disease_parameters(self, filename, config_override_data):
        """ Method to load in attributes from the disease configuration file.

        All parameters in the file are loaded into the object, and parameter names
        are taken from dictionary keys.

        Parameters
        ----------
        filename : str
            Path to the disease configuration file.
        config_override_data : dict
            Dictionary containing possible override versions of the secondary configuration files.
            Note, does not include paths to configuration files but the files themselves.

        """

        if config_override_data is not None:
            self.disease_parameters = config_override_data['disease_config_data']
        else:
            # If path is absolute, use it.
            if Path(filename).is_absolute():
                with open(filename, 'rb') as file:
                    self.disease_parameters = tomli.load(file)

            # Assume that the configuration filename is relative to path of main config.
            # If not set, assume relative to working directory.
            # Last attempt try relative to cv19 project directory.
            else:
                filepath = Path(self.config_dir, filename)
                try:
                    with open(filepath, 'rb') as file:
                        self.disease_parameters = tomli.load(file)

                except FileNotFoundError:
                    warnings.warn((f"Unable to find file: {filepath} "
                                   "assuming directory is relative to main config. "
                                   "Attempting read relative to CV19ROOT directory."))

                    filepath = Path(CV19ROOT, filename)
                    with open(filepath, 'rb') as file:
                        self.disease_parameters = tomli.load(file)

    def init_classes(self):
        """ Method that links the policy, population, and interaction sites class objects with
        the Simulation class (serves as pointer variables).
        """

        # Initalize the policy class
        self.policy = Policy(self)

        # Initialize the population
        self.pop = Population(self)

        # Initalize the interaction sites
        self.inter_sites = InteractionSites(self)

    def set_code_version(self):
        """Method to get and set the version of the code used to run the simulation.

        Note
        ----
        This function should really be using the --dirty flag, but only based
        on certain files. For example, local modifications to the notebook do not
        matter, whereas any modifications to the main classes could.
        """

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

    def make_tracking_df(self):
        """ Method to initalize the tracking dataframe for the simulation object
        """

        # Create a dictionary with tracking arrays and correct datatypes
        tracking_dict = {
            "new_infected": np.zeros(self.nDays, dtype=int),
            "delta_infected": np.zeros(self.nDays, dtype=int),
            "infected": np.zeros(self.nDays, dtype=int),
            "susceptible": np.zeros(self.nDays, dtype=int),
            "recovered": np.zeros(self.nDays, dtype=int),
            "dead": np.zeros(self.nDays, dtype=int),
            "hospitalized": np.zeros(self.nDays, dtype=int),
            "ICU": np.zeros(self.nDays, dtype=int),
            "quarantined": np.zeros(self.nDays, dtype=int),
            "new_quarantined": np.zeros(self.nDays, dtype=int),
            "tested": np.zeros(self.nDays, dtype=int),
            "new_tested": np.zeros(self.nDays, dtype=int),
            "testing_wait_list": np.zeros(self.nDays, dtype=int),
            "inf_students": np.zeros(self.nDays, dtype=int),
            "masks": np.zeros(self.nDays, dtype=bool),
            "lockdown": np.zeros(self.nDays, dtype=bool),
            "testing": np.zeros(self.nDays, dtype=bool),
            "time": np.zeros(self.nDays, dtype=float),
            "R0": np.zeros(self.nDays, dtype=float),
            "R_eff": np.zeros(self.nDays, dtype=float),
            "HIT": np.zeros(self.nDays, dtype=float),
            "vaccinated": np.zeros(self.nDays, dtype=int),
            "gamma": np.zeros(self.nDays, dtype=float),
            "beta": np.zeros(self.nDays, dtype=float),
            "n_interactions": np.zeros(self.nDays, dtype=int),
        }

        # Convert to a DataFrame object
        self.tracking_df = pd.DataFrame(tracking_dict)

    def run(self, fail_on_rerun=True):
        """ Method that runs the monte-carlo simulation.

        This is the main function in the Simulation class that generates the tracking data. The
        fail_on_rerun parameter is added to make sure that data from previous runs is not overwritten
        by running the simulation again.

        Parameters
        ----------
        fail_on_rerun : bool
            Variable to indicate whether the code should return an error if same object is
            run multiple times.
        """

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

            # UPDATE TRACKING
            self.update_tracking_arrays(day)
            self.tracking_df.at[day, "hospitalized"] = self.pop.count_hospitalized()
            self.tracking_df.at[day, "mask_mandate"] = old_mask_mandate
            self.tracking_df.at[day, "lockdwn_mandate"] = old_lockdown_mandate
            self.tracking_df.at[day, "testing_mandate"] = old_testing_mandate

            # UPDATE POLICY
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

            # infect random students on the day they come in
            if self.inter_sites.students_on and day == self.policy.student_day_trigger:
                infStudents = np.random.randint(self.inf_students_lower, self.inf_students_upper)
                indices = np.random.choice(self.pop.get_student_indices(), infStudents, replace=False)
                # Convert virus type to virus code
                student_default_virus_code = self.variant_codes[self.student_default_virus_type]
                self.pop.infect_incoming_students(indices=indices, day=day, virus_type=student_default_virus_code)

            # ADD DAILY VISITORS
            self.pop.add_visitors(day)

            # UPDATE INTERACTION SITES
            self.inter_sites.daily_reset()

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
                tests_per_day = self.policy.get_num_tests(self.tracking_df.at[day, "quarantined"],
                                                          self.tracking_df.at[day, "new_quarantined"],
                                                          self.tracking_df.at[day, "testing_wait_list"])
                self.inter_sites.testing_site(tests_per_day, day)

            # Manage Quarantine
            self.pop.update_quarantine(day)

            # Manage Vaccines
            self.pop.update_vaccinated(day)

            # UPDATE POPULATION

            # remove the daily visitors
            self.pop.remove_visitors()

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

            self.tracking_df.at[day, "time"] = timer() - beg_time

            if self.verbose:
                print((f"Day: {day}, "
                       f"infected: {self.tracking_df.at[day, 'infected']}, "
                       f"recovered: {self.tracking_df.at[day, 'recovered']}, "
                       f"susceptible: {self.tracking_df.at[day, 'susceptible']}, "
                       f"dead: {self.tracking_df.at[day, 'dead']}, "
                       f"hospitalized: {self.tracking_df.at[day, 'hospitalized']}, "
                       f"ICU: {self.tracking_df.at[day, 'ICU']}, "
                       f"tested: {self.tracking_df.at[day, 'tested']}, "
                       f"total quarantined: {self.tracking_df.at[day, 'quarantined']}, "
                       f"infected students: {self.tracking_df.at[day, 'inf_students']}, "
                       f"vaccinated: {self.tracking_df.at[day, 'vaccinated']}"))

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
            print(f"    {self.tracking_df['susceptible'].iloc[-1]} never got it")
            print(f"    {self.tracking_df['dead'].iloc[-1]} died")
            print(f"    {self.tracking_df['infected'].max()} had it at the peak")
            print(f"    {self.tracking_df.at[day, 'tested']} were tested")
            print(f"    {self.tracking_df['quarantined'].max()} were in quarantine at the peak")
            print(f"    {self.tracking_df['hospitalized'].max()} at peak hospitalizations")
            print(f"    {self.tracking_df['dead'].max()} at peak deaths")
            print("    The breakdown of the variants is", end=": ")
            for key, val in self.track_virus_types.items():
                print(f"{key}-{np.max(val)}", end=", ")
            print("")
            print(f"    {self.tracking_df.at[day, 'vaccinated']} people were vaccinated")
            print(f"    {self.tracking_df.at[day, 'vaccinated']/self.nPop*100:.2f}% of population was vaccinated.")

        # Unpack the virus types into the dataframe
        for virus_type, virus_type_arr in self.track_virus_types.items():
            self.tracking_df.loc[:, virus_type] = virus_type_arr

        # Unpack the interaction site number of interactions into the dataframe
        for inter_site, inter_site_arr in self.inter_sites.daily_interactions.items():
            self.tracking_df.loc[:, f"n_interactions_{inter_site}"] = inter_site_arr

        # Change the index to day
        self.tracking_df.index.rename("day", inplace=True)

        self.has_run = True

    def update_tracking_arrays(self, day):
        """ Function to update the tracking dataframe after each day.

        Parameters
        ----------
        day : int
            The integer day that the simulation is currently being updated for. Used to know what entry
            in the dataframe to update.
        """

        # Count all the different states of people
        self.tracking_df.at[day, "infected"] = self.pop.count_infected()
        self.tracking_df.at[day, "recovered"] = self.pop.count_recovered()
        self.tracking_df.at[day, "dead"] = self.pop.count_dead()
        self.tracking_df.at[day, "hospitalized"] = self.pop.count_hospitalized()
        self.tracking_df.at[day, "ICU"] = self.pop.count_ICU()
        self.tracking_df.at[day, "tested"] = self.pop.count_tested()
        self.tracking_df.at[day, "quarantined"] = self.pop.count_quarantined()
        self.tracking_df.at[day, "testing_wait_list"] = self.pop.get_testing_wait_list()
        self.tracking_df.at[day, "new_quarantined"] = self.pop.get_new_quarantined()
        self.tracking_df.at[day, "infected_students"] = self.pop.count_infected_students()
        self.tracking_df.at[day, "vaccinated"] = self.pop.count_vaccinated()

        if day != 0:
            delta_infected = self.tracking_df.at[day, "infected"] - self.tracking_df.at[day - 1, "infected"]
            self.tracking_df.at[day, "delta_infected"] = delta_infected
            self.tracking_df.at[day, "new_infected"] = self.inter_sites.daily_new_infections
            new_tested = self.tracking_df.at[day, "tested"] - self.tracking_df.at[day - 1, "tested"]
            self.tracking_df.at[day, "new_tested"] = new_tested

            self.calculate_SIR_metrics(day)

        daily_variant_counts = self.pop.count_virus_types()
        for virus_name in self.virus_names:
            self.track_virus_types[virus_name][day] = daily_variant_counts[virus_name]

        self.new_tests = 0

    def calculate_SIR_metrics(self, day):
        """Method to caclulate all metrics related to SIR models.

        These variables are defined in the wikipedia page and are calculated as such. No variables are
        returned, all values are set inside the function in the tracking arrays.

        Wikipedia page link: https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology

        The following variables are calculated: gamma, beta, R0, R effective, and HIT (herd immunity threshold).
        """

        # Define variables in accordance with wikipedia page
        dR_dt = self.tracking_df.at[day, "recovered"] - self.tracking_df.at[day - 1, "recovered"]
        dI_dt = self.tracking_df.at[day, "delta_infected"]
        S, I = self.tracking_df.at[day, "susceptible"], self.tracking_df.at[day, "infected"]
        N = self.parameters["simulation_data"]["nPop"]

        gamma = dR_dt / I if I > 0 else 0
        beta = (dI_dt + gamma * I) * (N / (I * S)) if I * S > 0 else 0

        if day - self.R0_lag_time >= 0:

            # Use the old gamma (infected rate) and current beta (recovery rate)
            lagged_gamma = self.tracking_df.at[day - self.R0_lag_time, "gamma"]
            daily_R0 = beta / lagged_gamma if lagged_gamma != 0 else 0
            daily_R_eff = daily_R0 * (S / N)
            HIT = 1 - 1 / daily_R_eff if daily_R_eff != 0 else 1

            self.tracking_df.at[day, "R0"] = daily_R0
            self.tracking_df.at[day, "R_eff"] = daily_R_eff
            self.tracking_df.at[day, "HIT"] = HIT

        self.tracking_df.at[day, "gamma"], self.tracking_df.at[day, "beta"] = gamma, beta

    def check_has_run(self, check, information="", fail=True):
        """Method to check whether or not the simulation has run.

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
        """

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

    def plot(self, log=False, **kwargs):
        """ Method used to plot simulation results.

        Will return a warning or error if the simulation has not been run yet. For plotting the number of interactions,
        you must supply a list with the codes for the sites you wish to plot.

        Parameters
        ----------
        plot_* : bool
            Takes in a single variable for each tracking array held in the Simulation class object. The
            variable is of name plot_<tracked value name>, for example plot_hospitalized. Setting this
            parameter to `True` will plot the array, and `False` will not. An exception to this is when
            plotting virus_types and n_interactions, which should be tuples or lists of the
            appropriate keys for those variables.
        log : bool
            Indicate whether to plot with a log scale on the y-axis.
        """

        self.check_has_run(check=True, information="Cannot make plots.", fail=True)

        _, ax = plt.subplots(figsize=(10, 8), dpi=100)
        days = np.linspace(0, self.nDays, self.nDays, dtype=int)

        # Add the default values
        default_plotting_values = ['susceptible', 'infected', 'recovered', 'dead']
        for plotting_value in default_plotting_values:
            if kwargs.get(plotting_value, None) is None:
                kwargs[plotting_value] = True

        # List plotting values that use plt.fill_between
        fill_plotting_values = ["masks", "testing", "lockdown"]

        # Plot the standard arrays
        for parameter, value in kwargs.items():
            if value:
                # Handle nested variant plotting
                if parameter == "virus_types":
                    for vt_key, vt_value in value.items():
                        if vt_value:
                            plt.plot(days, self.tracking_df[vt_key],
                                     label=f"Virus Type: {vt_key}")

                # Handle nested interaction plotting
                elif parameter == "n_interactions":
                    for nint_key, nint_value in value.items():
                        if nint_value:
                            plt.plot(days, self.tracking_df[f"n_interactions_{nint_key}"],
                                     label=f"Total Interactions: {nint_key}")

                # Handle the fill_between plotting
                elif parameter in fill_plotting_values:
                    plt.fill_between(days, 0, 1, where=self.tracking_df[parameter], alpha=0.3,
                                     transform=ax.get_xaxis_transform(), label=f"{parameter} implemented")

                # Handle the regular plotting
                else:
                    plt.plot(days, self.tracking_df[parameter], label=parameter.replace("_", " "))

        # Final graph formatting
        plt.grid()
        plt.legend()
        if log:
            plt.yscale("log")
        plt.ylabel("People")
        plt.xlabel("Days")

    def get_tracking_dataframe(self):
        """ Method to return all tracking arrays as a pandas DataFrame.

        Returns
        -------
        self.tracking_df : `pd.DataFrame`
            A pandas DataFrame holding all the tracking arrays from the simulation.
        """
        self.check_has_run(check=True,
                           information="Cannot return zero-initialized arrays.",
                           fail=True)

        return self.tracking_df

    def get_tracking_arrays(self):
        """ Method to return all tracking arrays as a dictionary of lists.

        Returns
        -------
        self.tracking_df : dict of lists
            A dictionary of lists that contain the same content as the self.tracking_df DataFrame.
        """
        return self.get_tracking_dataframe().to_dict("list")
