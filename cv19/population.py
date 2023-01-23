from random import random, sample
import tomli

import numpy as np

from .data import constants
from .person import Person

# This value means that the person index at this location is not susceptible/infected/dead/...
# All arrays are intialized to this (except healthy, as everyone is healthy)
NULL_ID = -1


class Population:
    '''Creates a population of people based on the total population
     uses and age distrubution to weight the assignment of ages.

     Susceptible list has negative values for infected, and positive indicies for suseptible.
     Infected list has negative values for healthy, and positive indicies for infected.
     Recovered list has negative values for not recovered, and postitive indicies for
     recovered.
     '''

    def __init__(self, sim_obj):
        ''' __init__ method docstring.

        Parameters
        ----------
        sim_obj : :obj:`population class`
            The encompassing simulation object hosting the population class.
        '''

        # Set attributes from sim_obj file
        self.load_attributes_from_sim_obj(sim_obj)

        # Actually set all of these values
        self.set_demographic_parameters()

        self.nPop = sim_obj.nPop  # total population

        # Student parameter
        self.nStudents = sim_obj.num_students  # full capacity ~ 24k students

        self.population = [0] * self.nPop  # The list of all people
        self.household = [0] * self.nPop  # list of non-student houses (list that contains all lists of the people in the house)
        self.students = [0] * self.nStudents  # The list of only students
        self.stud_houses = [0] * self.nStudents  # list of student houses
        self.prob_of_test = self.prob_of_test
        self.prob_has_mask = self.prob_has_mask
        self.n_students_in_res = 0

        # For access to virus code mappings
        self.virus_codes = sim_obj.variant_codes

        houseIndex = 0
        totalHouse = 0
        while totalHouse < self.nPop - self.nStudents:
            houseSize = np.random.choice(a=self.house_options, p=self.house_weights)
            totalHouse += houseSize
            self.household[houseIndex] = houseSize
            houseIndex += 1
        # Trim the last house if there's too many people in it for the population
        if totalHouse > self.nPop - self.nStudents:
            self.household[houseIndex - 1] -= totalHouse - (self.nPop - self.nStudents)
        # Slice household list to the right size
        self.household = self.household[:houseIndex]

        studHouseIndex = 0
        studTotalHouse = 0
        count = 0
        while studTotalHouse < self.nStudents:
            studHouseSize = np.random.choice(a=self.house_options, p=self.house_weights)
            studTotalHouse += studHouseSize
            self.stud_houses[studHouseIndex] = studHouseSize
            studHouseIndex += 1
            if studHouseSize == 1:
                count += 1
        # Trim the last house if there's too many people in it for the population
        if studTotalHouse > self.nStudents:
            self.stud_houses[studHouseIndex - 1] -= studTotalHouse - (self.nStudents)
        # Slice student houses list to the right size
        self.stud_houses = self.stud_houses[:studHouseIndex]

        # Initialize parameters of people immediately.
        # Much quick this way, utilizes numpy efficiency.
        age_arr = np.random.choice(a=self.age_options, p=self.age_weights, size=self.nPop)
        job_arr = np.random.choice(a=self.job_options, p=self.job_weights, size=self.nPop)
        isolation_tend_arr = np.random.choice(a=self.isolation_options, p=self.isolation_weights, size=self.nPop)
        case_severity_arr = np.empty(shape=self.nPop, dtype=object)
        # case severity now changes to depending on the age

        for i, age in enumerate(age_arr):
            try:
                case_severity_arr[i] = np.random.choice(a=self.severity_options,
                                                        p=[self.severity_params[age][key] for key in constants.SEVERITY_OPTIONS])
            except KeyError as e:
                raise ValueError((f"'{age}' is not a valid age range and has no associated case severity.")) from e

        mask_type_arr = np.random.choice(a=self.mask_options, p=self.mask_weights, size=self.nPop)
        has_mask_arr = np.random.uniform(size=self.nPop) < self.prob_has_mask
        
        #Prepare vaccination date array for population initialization
        vaccine_type_arr = np.random.choice(a=self.vaccine_options, p=self.vaccine_weights, size=self.nPop)
        vaccination_date_arr = self.set_v0_parameters(self,sim_obj)

        # Initialize the house index and size for the loop
        houseIndex = 0
        houseSize = self.household[houseIndex]

        for i in range(0, self.nPop - self.nStudents):
            # check if the house size is 0 at the beginning
            if houseSize == 0:
                houseIndex += 1
                houseSize = self.household[houseIndex]

            vaccine_type = vaccine_type_arr[i]  # vaccine type from vaccine type arr
            individual_vaccine_info = {"vaccine_type": vaccine_type,
                                       "vaccine_max_efficacy": self.vaccine_parameters["vaccine_max_efficacy"][vaccine_type],
                                       "vaccine_immunity_buildup_days": self.vaccine_parameters["vaccine_immunity_buildup_days"][vaccine_type],
                                       "long_term_vaccine_eff": self.vaccine_parameters["long_term_vaccine_eff"][vaccine_type],
                                       "vaccine_efficacy_min_day": self.vaccine_parameters["vaccine_efficacy_min_day"][vaccine_type]}
            # set up dictionary of vaccination parameters for immunization history object

            # MAKE A PERSON
            newPerson = Person(index=i,
                               sim_obj=sim_obj,
                               infected=False,
                               recovered=False,
                               dead=False,
                               hospitalized=False,
                               ICU=False,
                               quarantined=False,
                               quarantined_day=None,
                               infected_day=None,
                               recovered_day=None,
                               death_day=None,
                               others_infected=None,
                               cure_days=None,
                               recent_infections=None,
                               age=age_arr[i],
                               job=job_arr[i],
                               house_index=houseIndex,
                               vaccine_info=individual_vaccine_info,
                               isolation_tendencies=isolation_tend_arr[i],
                               case_severity=case_severity_arr[i],
                               mask_type=mask_type_arr[i],
                               has_mask=has_mask_arr[i],
                               virus_type=None)

            # ADD A PERSON
            self.population[i] = newPerson

            # Increment house info
            houseSize -= 1

        # Create the array to hold the indices of people in the house
        self.house_ppl_i = [np.tile(-1, size) for size in self.household]

        # add people indices to the housing list
        for i in range(0, self.nPop - self.nStudents):
            housei = self.population[i].household
            where = np.where(self.house_ppl_i[housei] == -1)[0][0]
            self.house_ppl_i[housei][where] = i

        # Students
        student_age = np.random.choice(a=['10-19', '20-29'], p=[0.5, 0.5], size=self.nStudents)  # students age ranges 10-19 and 20-29
        student_case_severity_arr = np.empty(self.nStudents, dtype=object)
        for i, age in enumerate(student_age):
            try:
                student_case_severity_arr[i] = np.random.choice(a=self.severity_options,
                                                                p=[self.severity_params[age][key]
                                                                   for key in constants.SEVERITY_OPTIONS])
            except KeyError as e:
                raise ValueError((f"'{age}' is not a valid age range and has no associated case severity.")) from e

        self.student_indices = np.zeros(self.nPop, dtype=int) + NULL_ID
        self.res_houses = np.zeros(len(self.stud_houses), dtype=int) + NULL_ID  # student houses that are in residence will be nonzero

        studHouseIndex = 0
        studHouseSize = self.stud_houses[studHouseIndex]

        for i in range(self.nPop - self.nStudents, self.nPop):
            # check if the house size is 0 at the beginning
            if studHouseSize == 0:
                studHouseIndex += 1
                studHouseSize = self.stud_houses[studHouseIndex]

            vaccine_type = vaccine_type_arr[i]
            individual_vaccine_info = {"vaccine_type": vaccine_type,
                                       "vaccine_max_efficacy": self.vaccine_parameters["vaccine_max_efficacy"][vaccine_type],
                                       "vaccine_immunity_buildup_days": self.vaccine_parameters["vaccine_immunity_buildup_days"][vaccine_type],
                                       "long_term_vaccine_eff": self.vaccine_parameters["long_term_vaccine_eff"][vaccine_type],
                                       "vaccine_efficacy_min_day": self.vaccine_parameters["vaccine_efficacy_min_day"][vaccine_type]}  # set up immunization history object parameters as dictionary

            newStudent = Person(index=i,
                                sim_obj=sim_obj,
                                infected=False,
                                recovered=False,
                                dead=False,
                                hospitalized=False,
                                ICU=False,
                                quarantined=False,
                                quarantined_day=None,
                                infected_day=None,
                                recovered_day=None,
                                death_day=None,
                                others_infected=None,
                                cure_days=None,
                                recent_infections=None,
                                age=student_age[i - self.nPop + self.nStudents],  # adjust for index inconsistency
                                job='Student',
                                house_index=studHouseIndex,
                                vaccine_info=individual_vaccine_info,
                                isolation_tendencies=isolation_tend_arr[i],
                                case_severity=student_case_severity_arr[i - self.nPop + self.nStudents],  # adjust for index inconsistency
                                mask_type=mask_type_arr[i],
                                has_mask=has_mask_arr[i],
                                virus_type=None)

            self.population[i] = newStudent

            self.student_indices[i] = i  # set their student status

            # Increment house info
            studHouseSize -= 1

        # Create the array to hold the indices of people in the house
        self.house_stud_i = [np.tile(-1, size) for size in self.stud_houses]

        # create the residence list
        # this is probably not the most efficient it could be
        for house_size in range(1, 3):
            for i, stud_house_size in enumerate(self.stud_houses):
                # If the student house only has 1 person, add it to the residence list
                if stud_house_size == house_size:
                    if self.n_students_in_res >= (sim_obj.max_num_res_students - 1):
                        break
                    self.res_houses[i] = i
                    self.n_students_in_res += house_size
            if self.n_students_in_res >= (sim_obj.max_num_res_students - 1):
                break

        # Add the people indices to the list
        for i in range(self.nPop - self.nStudents, self.nPop):
            housei = self.population[i].household
            where = np.where(self.house_stud_i[housei] == -1)[0][0]
            self.house_stud_i[housei][where] = i

        # Create person status arrays
        # A non-negative index indicates that they are the property,
        # NULL_ID (-1) indicates that they are /not/ the property.
        self.susceptible = np.array(range(self.nPop), dtype=int)  # list of all susceptible individuals
        self.infected = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of all infected people
        self.recovered = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of recovered people
        self.dead = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of dead people
        self.knows_infected = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people with positive test and still infected
        self.hospitalized = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people hospitalized and in the ICU
        self.ICU = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people in the ICU
        self.quarantined = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people who are currently in quarantine
        self.virus_types = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of individuals with NULL_ID as virus type
        self.vaccinated = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people who have been vaccinated
        self.testing = []  # list of people waiting to be tested
        self.test_sum = 0  # total number of tests that have been run
        self.quarantined_sum = 0  # total number of people in quarantine (created as the list was having indexing issues)
        self.new_quarantined_num = 0  # new people in quarantine

        # Infect the first n0 people for each virus type
        total_n0 = sum(v_id for _, v_id in sim_obj.variants.items())
        init_infect_count, total_indices = 0, sample(range(self.nPop), total_n0)
        for virus_name in sim_obj.variants.keys():
            virus_code = sim_obj.variant_codes[virus_name]
            variant_infections = sim_obj.variants[virus_name]

            for index_count in range(init_infect_count, init_infect_count + variant_infections):
                i = total_indices[index_count]
                self.population[i].infect(day=0, virus_type=virus_code)
                self.infected[i] = i
                self.virus_types[i] = virus_code
                self.susceptible[i] = NULL_ID
            init_infect_count += variant_infections

        # Vaccinate first v0 people
        v_indices = sample(range(self.nPop), self.v0)
        for i,v in enumerate(v_indices):
        # set vaccinated date based on vaccination_date_arr
            self.population[v].immunization_history_obj.set_vaccinated(day=int(vaccination_date_arr[i]))
            self.vaccinated[v] = v

    def load_attributes_from_sim_obj(self, sim_obj):
        '''Method to load in attributes from the provided simulation class object.

        Sets all objects in the "population_data" dictionary key as self
        attributes of the population class.

        Parameters
        ----------
        sim_obj : :obj:`cv19.simulation.simulation`
            The encompassing simulation object hosting the simulation.
        '''

        # making sim_obj accessible
        self.sim_obj = sim_obj

        attributes = sim_obj.parameters["population_data"].keys()
        for attr in attributes:
            setattr(self, attr, sim_obj.parameters["population_data"][attr])

        self.variant_codes = sim_obj.variant_codes

        # case severity from disease params
        self.severity_options = constants.SEVERITY_OPTIONS

        # assign severity weights
        with open(self.case_severity_file, 'rb') as toml_file:
            self.severity_params = tomli.load(toml_file)

        # format mask weights correctly
        self.mask_weights = np.array([self.mask_type[key] for key in constants.MASK_OPTIONS])
        self.mask_options = constants.MASK_OPTIONS

        # format vaccine parameters
        self.vaccine_weights = np.array([self.sim_obj.vaccine_type[key] for key in constants.VACCINE_OPTIONS])
        self.vaccine_options = constants.VACCINE_OPTIONS
        self.vaccine_parameters = sim_obj.immunization_history_parameters

    def set_demographic_parameters(self):
        '''Method to open disease parameters from the TOML file.

        Sets all constants in the population class as self attributes of the population class.
        '''

        with open(self.demographics_file, 'rb') as toml_file:
            disease_params = tomli.load(toml_file)

        self.age_options = constants.AGE_OPTIONS
        self.job_options = constants.JOB_OPTIONS
        self.house_options = constants.HOUSE_OPTIONS
        self.isolation_options = constants.ISOLATION_OPTIONS

        # Isolation #
        self.isolation_weights = np.ones(len(self.isolation_options))
        # Normalize the probability
        self.isolation_weights /= float(sum(self.isolation_weights))  # this is the one we don't have data on yet

        # PULL DATA FROM THE TOML FILE #
        # age #
        self.age_weights = np.array([disease_params['age_weights'][age_range]
                                     for age_range in self.age_options])

        # Job #
        self.job_weights = np.array([disease_params['job_weights'][job_type]
                                     for job_type in self.job_options])

        # House #
        self.house_weights = np.array([disease_params['house_weights'][house_size]
                                       for house_size in self.house_options])

        # Cast this so they can be used as ints
        self.house_options = [int(x) for x in constants.HOUSE_OPTIONS]
        
    def set_v0_parameters(self,sim_obj):
        '''Method to set up initially vaccinated population array.
        
        Returns
        -------
        vaccination_date_arr: :obj:`np.array` of :obj:`int`
        '''
        
        self.v0 = sim_obj.v0_parameters["v0"]  # initial vaccinated
        
        v0_lower = sim_obj.v0_parameters["v0_interval_start_day"]  # lower bound on v0 range
        v0_upper = sim_obj.v0_parameters["v0_interval_end_day"]  # upper bound on v0 range
        vaccination_date_arr = np.zeros(self.v0)  # initialize v0 dates array
        
        if v0_lower <= 0 and v0_upper <= 0:  # v0 bounds cannot be greater than 0

            if v0_lower < v0_upper:  # v0_lower should be smaller (more negative) than v0_upper
                vaccination_date_arr = np.random.uniform(low=v0_lower, high=v0_upper, size=self.v0)
                
            else:  # they are equal to each other:
                vaccination_date_arr = np.ones(self.v0) * v0_lower
                
        return vaccination_date_arr

    def get_population_size(self):
        '''Method to return population size.

        Returns
        -------
        self.nPop: `int`
        '''
        return self.nPop

    def get_population(self):
        '''Method to retrieve a list of the population.

        Returns
        -------
        self.has_mask: :obj:`np.array` of :obj:`int`
        '''
        return self.population

    def get_student_indices(self):
        '''Method to retrieve a list of the student indices.

        Returns
        -------
        self.has_mask: :obj:`np.array` of :obj:`int`
        '''
        return self.student_indices[self.student_indices != NULL_ID]

    def get_student_pop_size(self):
        '''Method to retrieve the number of students.

        Returns
        -------
        self.nStudents: :obj:`int`
        '''
        return self.nStudents

    def remove_visitors(self, indices):
        '''Method to remove visitors from the simulation.
        '''
        for i in sorted(indices, reverse=True):
            self.population.pop(i)

        if len(self.population) != self.nPop:
            raise RuntimeError(("Population is not expected length after removing visitors "
                               f"(expected {self.nPop}, is {len(self.population)})."))

    def get_susceptible(self):
        '''Method to retrieve indicies of people suseptible.

        Returns
        -------
        self.suseptible[self.suseptible != NULL_ID]: :obj:`np.array` of :obj:`int`
        '''
        return self.susceptible[self.susceptible != NULL_ID]

    def get_infected(self):
        '''Method to retrieve indicies of people infected.

        Returns
        -------
        self.infected[self.infected != NULL_ID]: :obj:`np.array` of :obj:`int`
        '''
        return self.infected[self.infected != NULL_ID]

    def get_recovered(self):
        '''Method to retrieve indicies of people recovered.

        Returns
        -------
        self.recovered[self.recovered != NULL_ID]: :obj:`np.array` of :obj:`int`
        '''
        return self.recovered[self.recovered != NULL_ID]

    def get_dead(self):
        '''Method to retrieve indicies of dead people.

        Returns
        -------
        self.dead[self.dead != NULL_ID]: :obj:`np.array` of :obj:`int`
        '''
        return self.dead[self.dead != NULL_ID]

    def get_hospitalized(self):
        '''Method to retrieve indicies of the people hospitalized.

        Returns
        -------
        self.hospitalized[self.hospitalized != NULL_ID]: :obj:`np.array` of :obj:`int`
        '''
        return self.hospitalized[self.hospitalized != NULL_ID]

    def get_ICU(self):
        '''Method to retrieve indicies of the people in the ICU.

        Returns
        -------
        self.ICU[self.ICU != NULL_ID]: :obj:`np.array` of :obj:`int`
        '''
        return self.ICU[self.ICU != NULL_ID]

    def get_quarantined(self):
        '''Method to retrieve indicies of the people in quarantining.

        Returns
        -------
        self.quarantined[self.quarantined != NULL_ID]: :obj:`np.array` of :obj:`int`
        '''
        return self.quarantined[self.quarantined != NULL_ID]

    def get_residences(self):
        '''Method to retrieve a list of the houses that are part of the residences.

        Returns
        -------
        self.res_houses: :obj:`np.array` of :obj:`int`
        '''
        return self.res_houses[self.res_houses != NULL_ID]

    def get_res_size(self):
        '''Method to retrieve the number of students in residence.

        Returns
        -------
        self.n_students_in_res: :obj:`int`
        '''
        return self.n_students_in_res

    def count_susceptible(self):
        '''Method to count the number of people susceptible in each bin.

        Returns
        -------
        np.count_nonzero(self.suseptible != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.susceptible != NULL_ID)

    def count_infected(self):
        '''Method to count the number of people infected.

        Returns
        -------
        np.count_nonzero(self.infetced != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.infected != NULL_ID)

    def count_variant_cases(self, virus_name):
        '''Method to count the number of people infected with a certain variant.

        Returns
        -------
        np.count_nonzero(self.infetced != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        virus_code = self.virus_codes[virus_name]
        return np.count_nonzero(self.virus_types == virus_code)

    def count_infected_students(self):
        '''Method to count how many infected students there are.

        Returns
        -------
        np.count_nonzero(np.logical_and(self.student_indices != NULL_ID, self.infected != NULL_ID)): :obj:`int`
        '''
        return np.count_nonzero(np.logical_and(self.student_indices != NULL_ID, self.infected != NULL_ID))

    def count_recovered(self):
        '''Method to count the number of people recovered.

        Returns
        -------
        np.count_nonzero(self.recovered != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.recovered != NULL_ID)

    def count_dead(self):
        '''Method to count the number of people dead.

        Returns
        -------
        np.count_nonzero(self.dead != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.dead != NULL_ID)

    def count_hospitalized(self):
        '''Method to count the number of people in the hospital.

        Returns
        -------
        np.count_nonzero(self.hospitalized != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.hospitalized != NULL_ID)

    def count_ICU(self):
        '''Method to count the number of people in the ICU.

        Returns
        -------
        np.count_nonzero(self.ICU != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.ICU != NULL_ID)

    def count_quarantined(self):
        '''Method to count the number of people quarantining.

        Returns
        -------
        np.count_nonzero(self.quarantined != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.quarantined != NULL_ID)

    def count_masks(self):
        '''Method to count the number of people wearing masks.

        Returns
        -------
        np.count_nonzero(self.has_mask > 0): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.has_mask > 0)

    def count_virus_types(self):
        '''Method to count all virus types and return them as a dictionary.

        Returns
        -------
        counts : :obj:`dict`
        '''
        counts = {virus_type: np.count_nonzero(self.virus_types == virus_code)
                  for virus_type, virus_code in self.variant_codes.items()}
        return counts

    def get_person(self, index):
        '''Method to return an individual based on their index.

        Returns
        -------
        np.population[index]: :obj:`int`
        '''
        return self.population[index]

    def infect(self, index, day, virus_type):
        '''Method to infect a person.

        Parameters
        ----------
        index : int
            The index of the person to be infected.
        day : int
            The day value that this function is being called on in the encompassing simulation class.

        Returns
        -------
        didWork: :obj:`int`
        '''

        # Convert to virus code if virus type is a string
        if isinstance(virus_type, str):
            virus_type = self.virus_codes[virus_type]

        didWork = self.population[index].infect(day=day, virus_type=virus_type)
        if didWork:
            self.infected[index] = index
            self.susceptible[index] = NULL_ID
            self.virus_types[index] = virus_type
            if self.population[index].ICU:
                self.ICU[index] = index
            elif self.population[index].hospitalized:
                self.hospitalized[index] = index

        return didWork

    def infect_incoming_students(self, indices, day, virus_type):
        '''Method to infect incoming students to the simulation.

        Parameters
        ----------
        indices : `np.array` of `int`
            The indices of the students added to the population to be infected.
        day : int
            The day value that this function is being called on in the encompassing simulation class.

        Returns
        -------
        : :obj:`bool`
            True to infect the student.
        '''

        for i in indices:
            daysAgo = np.random.randint(13)
            self.infect(index=i, day=day - daysAgo, virus_type=virus_type)
        return True

    def update_infected(self, index):
        '''Method to update the list of the infected population at the specified index.

        Parameters
        ----------
        index : int
            The index of the person in the population to be infected.

        Returns
        -------
        : :obj:`bool`
            True if the value at the index in the infected list was changed, False if it was not changed.
        '''

        if self.infected[index] == index or self.susceptible[index] == NULL_ID or not self.population[index].is_infected():
            # Already infected, or cant be infected
            return False
        self.infected[index] = index
        self.susceptible[index] = NULL_ID
        return True

    def cure(self, index, day):
        '''Method to cure a person.

        Parameters
        ----------
        index : int
            The index of the person to be cured.
        day : int
            The day value that this function is being called on in the encompassing simulation class.

        Returns
        -------
        didWork: :obj:`int`
        '''

        didWork = self.population[index].check_cured(day)
        if didWork:
            self.infected[index] = NULL_ID
            self.recovered[index] = index
        return didWork

    def update_cured(self, index):
        '''Method to update the list of the already cured population.

        Parameters
        ----------
        index : int
            The index of the person in the population to be cured.

        Returns
        -------
        : :obj:`bool`
            True if the value at the index in the cured list was changed, False if it was not changed.
        '''

        if self.recovered[index] == index or not self.population[index].is_recovered():
            # Already recovered in pop obj or person obj is not actually recovered
            return False
        self.infected[index] = NULL_ID
        self.recovered[index] = index
        self.hospitalized[index] = NULL_ID
        self.virus_types[index] = NULL_ID
        self.ICU[index] = NULL_ID
        return True

    def die(self, index, day):
        '''Method to kill a person if they should be dead.

        Parameters
        ----------
        index : int
            The index of the person in the population who is meant to die.
        day : int
            The day value that this function is being called on in the encompassing simulation class.

        Returns
        -------
        didWork: :obj:`bool`
        '''

        didWork = self.population[index].check_dead(day)
        if didWork:
            self.infected[index] = NULL_ID
            self.recovered[index] = NULL_ID
            self.dead[index] = index
        return didWork

    def update_dead(self, index):
        '''Method to update the list of the dead population at the specified index.

        Parameters
        ----------
        index : int
            The index of the person in the population who is meant to die.

        Returns
        -------
        : :obj:`bool`
            True if the value at the index in the dead list was changed, False if it was not changed.
        '''

        if self.dead[index] == index or not self.population[index].is_dead():
            return False
        self.infected[index] = NULL_ID
        self.recovered[index] = NULL_ID
        self.hospitalized[index] = NULL_ID
        self.virus_types[index] = NULL_ID
        self.ICU[index] = NULL_ID
        self.dead[index] = index
        return True

    def update_quarantine(self, day):
        '''Method to release everyone who has done their quarantine. This does not add new people to the list.

        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.
        '''

        for i in self.get_quarantined():
            # Check their status
            if self.population[i].leave_quarantine(day):
                self.quarantined[i] = NULL_ID

    def get_new_quarantined(self):
        '''Method that retreves the number of new people quarantined that day.

        Returns
        -------
        self.new_quarantined_num: :obj:`int`
        '''
        return self.new_quarantined_num

    def count_tested(self):
        '''Method that retreves the total number of people tested.

        Returns
        -------
        self.test_sum: :obj:`int`
        '''
        return self.test_sum

    def update_uninfected_symptomatics(self):
        '''Method that causes a random sample of people to develop cold like symptoms.
        '''

        for person in self.population:
            person.update_uninfected_symptomatic()

    def update_infected_symptomatics(self, day):
        '''Method to add people to the testing waitlist based on their symptoms.

        First iterates through the entire population to check who should be allowed to test again. Calling
        the `person.has_been_tested_recently` function updates the testing ability of that person based on the day,
        and returns `True` if that person can test again and `False` if not.

        The rest of the code creates a list of all people who could possibly be symptomatic and can test.
        This list is looped through to judge whether a person should be added to the testing list.

        Parameters
        ----------
        day: int
            The current day the simulation is on.
        '''

        people_to_check = (person_id for person_id, person in enumerate(self.population[:self.nPop])
                           if person.could_be_symptomatic() and not person.has_been_tested_recently(day))

        for person_id in people_to_check:
            # Check if they are showing symptoms and update their status
            if self.population[person_id].check_symptoms(day):
                person = self.get_person(person_id)

                # Calculate if they should be tested again
                not_in_testing = person_id not in self.testing
                will_comply = (random() / person.get_protocol_compliance()) < self.prob_of_test

                if not_in_testing and will_comply:
                    self.testing.append(person_id)

    def get_testing_wait_list(self):
        '''Method to return number of people waiting to be tested.

        Returns
        -------
        len(self.testing): :obj:`int`
        '''
        return len(self.testing)

    def get_tested(self, n_tests_max, day):
        '''Method to test people in the testing waitlist.

        Parameters
        ----------
        tests_per_day: int
            Paramter gives the number of tests run.
        day: int
            The day the testing is being done on.
        '''

        # If less people are on the wait list than the testing capacity, test everyone.
        n_tests = min(len(self.testing), n_tests_max)
        self.test_sum += n_tests

        # Reset number of newly quarantined people.
        self.new_quarantined_num = 0

        num_contacts_traced = 0
        for _ in range(n_tests):
            # Gets first person in the testing wait list and removes them.
            person_index = self.testing.pop(0)
            person = self.population[person_index]
            person.set_test_day(day)

            # Assumes tests are 100% accurate, does not account for false negatives.
            # TODO: implement a parameter for the testing accuracy.
            if person.infected:
                person.knows_infected = True

                # Quarantines the person.
                person.set_quarantine(day)
                self.new_quarantined_num += 1

                # Contact tracing.
                if self.ct_enabled and num_contacts_traced < self.ct_capacity:
                    person.contact_tracing(day=day)
                    num_contacts_traced += 1

            else:
                person.knows_infected = False

    def get_vaccinated(self):
        '''Method to retrieve indicies of people vaccinated.

        Returns
        -------
        self.vaccinated[self.vaccinated != NULL_ID]: :obj:`np.array` of :obj:`int`
        '''
        return self.vaccinated[self.vaccinated != NULL_ID]

    def count_vaccinated(self):
        '''Method to count the number of people vaccinated.

        Returns
        -------
        np.count_nonzero(self.vaccinated != NULL_ID): :obj:`np.array` of :obj:`int`
        '''
        return np.count_nonzero(self.vaccinated != NULL_ID)

    def update_vaccinated(self, day):
        '''Method to add people to the list of vaccinated people.

        Parameters
        ----------
        day : int
            The day the testing is being done on.
        '''

        non_vaccinated = np.array([index for index in range(self.nPop)
                                   if not self.population[index].immunization_history_obj.is_vaccinated()])

        num_vacc = self.sim_obj.num_vaccinations
        num_to_vaccinate = num_vacc if len(non_vaccinated) >= num_vacc else len(non_vaccinated)
        will_vaccinate = np.random.choice(range(len(non_vaccinated)), num_to_vaccinate, replace=False)
        self.to_vaccinate = non_vaccinated[will_vaccinate.astype(int)]

        for index in self.to_vaccinate:
            person_to_vaccinate = self.population[index]

            person_to_vaccinate.immunization_history_obj.set_vaccinated(day)
            self.vaccinated[index] = index

    def change_mask_wearing(self):
        '''Method to mandate wearing a mask.

        Parameters
        ----------
        has_mask: bool
        '''
        for person in self.population:
            person.has_mask = True
