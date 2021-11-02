import json
import random
import numpy as np
from .data import constants
from .person import Person

NULL_ID = -1 # This value means that the person index at this location is not susceptible/infected/dead/...
             # All arrays are intialized to this (except healthy, as everyone is healthy)

class Population:
    '''Creates a population of people based on the total population
     uses and age distrubution to weight the assignment of ages

     suscept list has negative values for infected, and positive indicies for susept
     infected list has negative values for healthy, and positive indicies for infected
     recovered list has negative values for not recovered, and postitive indicies for
     recovered
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
        self.n0 = sim_obj.n0  # initial infected
        #self.v0 = sim_obj.v0 # initial vaccinated
        #self.vPop = sim_obj.vPop

        # Student parameter
        self.nStudents = sim_obj.num_students # full capacity ~ 24k students

        self.population = [0] * self.nPop  # The list of all people
        self.household = [0] * self.nPop # list of non-student houses (list that contains all lists of the people in the house)
        self.students = [0] * self.nStudents # The list of only students
        self.stud_houses = [0] * self.nStudents # list of student houses
        self.prob_of_test = self.prob_of_test
        self.prob_has_mask = self.prob_has_mask
        self.max_vaccinations = self.max_vaccinations
        self.num_vaccinations = self.num_vaccinations
        self.n_students_in_res = 0

        houseIndex = 0
        totalHouse = 0
        while totalHouse < self.nPop-self.nStudents:
            houseSize = np.random.choice(a=self.house_options, p=self.house_weights)
            totalHouse += houseSize
            self.household[houseIndex] = houseSize
            houseIndex += 1
        # Trim the last house if there's too many people in it for the population
        if totalHouse > self.nPop-self.nStudents:
            self.household[houseIndex-1] -= totalHouse - (self.nPop-self.nStudents)
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
                count +=1
        # Trim the last house if there's too many people in it for the population
        if studTotalHouse > self.nStudents:
            self.stud_houses[studHouseIndex-1] -= studTotalHouse - (self.nStudents)
        # Slice student houses list to the right size
        self.stud_houses = self.stud_houses[:studHouseIndex]

        # Initialize parameters of people immediately.
        # Much quick this way, utilizes numpy efficiency.
        age_arr = np.random.choice(a=self.age_options, p=self.age_weights, size=self.nPop)
        job_arr = np.random.choice(a=self.job_options, p=self.job_weights, size=self.nPop)
        isolation_tend_arr = np.random.choice(a=self.isolation_options, p=self.isolation_weights, size=self.nPop)
        case_severity_arr = np.random.choice(a=self.severity_options, p=self.severity_weights, size=self.nPop)
        mask_type_arr = np.random.choice(a=self.mask_options, p=self.mask_weights, size=self.nPop)
        has_mask_arr = np.random.uniform(size=self.nPop) < self.prob_has_mask
        vaccine_type_arr = np.random.choice(a=self.vaccine_options, p=self.vaccine_weights, size=self.nPop)

        # Initialize the house index and size for the loop
        houseIndex = 0
        houseSize = self.household[houseIndex]

        for i in range(0, self.nPop-self.nStudents):
            # check if the house size is 0 at the beginning
            if houseSize == 0:
                houseIndex += 1
                houseSize = self.household[houseIndex]

            # MAKE A PERSON
            newPerson = Person(index=i, sim_obj=sim_obj, infected=False, recovered=False,
                               dead=False, hospitalized=False, ICU=False,
                               quarantined=False, quarantined_day=None,
                               infected_day=None, recovered_day=None, death_day=None,
                               others_infected=None, cure_days=None, recent_infections=None,
                               vaccinated=False, vaccine_type=vaccine_type_arr[i],
                               age=age_arr[i], job=job_arr[i], house_index=houseIndex,
                               isolation_tendencies=isolation_tend_arr[i],
                               case_severity=case_severity_arr[i], mask_type=mask_type_arr[i],
                               has_mask=has_mask_arr[i])

            # ADD A PERSON
            self.population[i] = newPerson

            # Increment house info
            houseSize -= 1

        # Create the array to hold the indices of people in the house
        self.house_ppl_i = [np.tile(-1, size) for size in self.household]

        # add people indices to the housing list
        for i in range(0, self.nPop-self.nStudents):
            housei = self.population[i].household
            where = np.where(self.house_ppl_i[housei] == -1)[0][0]
            self.house_ppl_i[housei][where] = i

        ############### STUDENTS ###############
        student_age = np.random.choice(a=['10-19', '20-29'], p=[0.5,0.5], size = self.nPop) # students are in age ranges 10-19 and 20-29

        self.student_indices = np.zeros(self.nPop, dtype=int) + NULL_ID
        self.res_houses = np.zeros(len(self.stud_houses), dtype=int) + NULL_ID # student houses that are in residence will be nonzero

        studHouseIndex = 0
        studHouseSize = self.stud_houses[studHouseIndex]

        for i in range(self.nPop-self.nStudents, self.nPop):
            # check if the house size is 0 at the beginning
            if studHouseSize == 0:
                studHouseIndex += 1
                studHouseSize = self.stud_houses[studHouseIndex]

            newStudent = Person(index=i, sim_obj=sim_obj, infected=False, recovered=False,
                                dead=False, hospitalized=False,ICU=False,quarantined=False,quarantined_day=None,
                                infected_day=None, recovered_day=None, death_day=None,
                                others_infected=None, cure_days=None, recent_infections=None,
                                vaccinated=False, vaccine_type=vaccine_type_arr[i],
                                age=student_age[i], job='Student', house_index=studHouseIndex,
                                isolation_tendencies=isolation_tend_arr[i],
                                case_severity=case_severity_arr[i],
                                has_mask=has_mask_arr[i])
            self.population[i] = newStudent

            self.student_indices[i] = i  # set their student status

            # Increment house info
            studHouseSize -= 1

        # Create the array to hold the indices of people in the house
        self.house_stud_i = [np.tile(-1, size) for size in self.stud_houses]

        # create the residence list
        # this is probably not the most efficient it could be
        for house_size in range(1,3):
            for i, stud_house_size in enumerate(self.stud_houses):
                # If the student house only has 1 person, add it to the residence list
                if stud_house_size == house_size:
                    if self.n_students_in_res >= (sim_obj.max_num_res_students-1):
                        break
                    self.res_houses[i] = i
                    self.n_students_in_res += house_size
            if self.n_students_in_res >= (sim_obj.max_num_res_students-1):
                break

        # Add the people indices to the list
        for i in range(self.nPop-self.nStudents, self.nPop):
            housei = self.population[i].household
            where = np.where(self.house_stud_i[housei] == -1)[0][0]
            self.house_stud_i[housei][where] = i

        # Create person status arrays
        self.susceptible = np.array(range(self.nPop), dtype=int)  #list of all susceptible individuals
        self.infected = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of all infected people
        self.recovered = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of recovered people
        self.dead = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of recovered people
        self.have_been_tested = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people who have been tested
        self.knows_infected = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people with positive test and still infected
        self.hospitalized = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people hospitalized and in the ICU
        self.ICU = np.zeros(self.nPop, dtype=int) + NULL_ID  # list of people in the ICU
        self.quarantined = np.zeros(self.nPop, dtype=int) + NULL_ID  #list of people who are currently in quarantine
        self.vaccinated = np.zeros(self.nPop, dtype=int) + NULL_ID # list of people who have been vaccinated

        self.testing = []  # list of people waiting to be others_infected
        self.test_sum = 0  # total number of tests that have been run
        self.quarantined_sum = 0  # total number of people in quarantine (created as the list was having indexing issues)
        self.new_quarantined_num = 0  # new people in quarantine

        # Selects the indices of the n0 initially infected people
        # at random, then infects them
        indices = random.sample(range(self.nPop), self.n0)
        for i in indices:
            self.population[i].infect(day=0)
            self.infected[i] = i
            self.susceptible[i] = NULL_ID

        # Vaccinate first v0 people
        #for i in range(self.v0):
            #self.vaccinated[i] = i

    def load_attributes_from_sim_obj(self, sim_obj):
        '''Method to load in attributes from the provided simulation class object.

        Sets all objects in the "population_data" dictionary key as self
        attributes of the population class.

        Parameters
        ----------
        sim_obj : :obj:`simulation class`
            The encompassing simulation object hosting the simulation.
        '''
        attributes = sim_obj.parameters["population_data"].keys()
        for attr in attributes:
            setattr(self, attr, sim_obj.parameters["population_data"][attr])

        # case severity from disease params
        self.severity_weights = np.array([sim_obj.disease_parameters["case_severity"][key]
                                          for key in constants.SEVERITY_OPTIONS])
        self.severity_options = constants.SEVERITY_OPTIONS

        # format mask weights correctly
        self.mask_weights = np.array([self.mask_type[key] for key in constants.MASK_OPTIONS])
        self.mask_options = constants.MASK_OPTIONS

        # format vaccine weights #
        self.vaccine_weights = np.array([self.vaccine_type[key] for key in constants.VACCINE_OPTIONS])
        self.vaccine_options = constants.VACCINE_OPTIONS

    def set_demographic_parameters(self):
        '''Method to open disease parameters from the json file.

        Sets all constants in the population class as self attributes of the population class.
        '''
        with open(self.demographics_file, encoding='utf-8') as json_file:
            disease_params = json.load(json_file)

        self.age_options = constants.AGE_OPTIONS
        self.job_options = constants.JOB_OPTIONS
        self.house_options = constants.HOUSE_OPTIONS
        self.isolation_options = constants.ISOLATION_OPTIONS

        # isolation #
        self.isolation_weights = np.ones(len(self.isolation_options))
        # Normalize the probability
        self.isolation_weights /= float(sum(self.isolation_weights))  #this is the one we don't have data on yet

        # PULL DATA FROM THE JSON FILE #
        # age #
        self.age_weights = np.array([disease_params['age_weights'][age_range]
                                     for age_range in self.age_options])

        # job #
        self.job_weights = np.array([disease_params['job_weights'][job_type]
                                     for job_type in self.job_options])

        # house #
        self.house_weights = np.array([disease_params['house_weights'][house_size]
                                       for house_size in self.house_options])

        # Cast this so they can be used as ints
        self.house_options = [int(x) for x in constants.HOUSE_OPTIONS]

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
        '''Method to retrieve a list of the student indices

        Returns
        -------
        self.has_mask: :obj:`np.array` of :obj:`int`
        '''
        return self.student_indices[self.student_indices != NULL_ID]

    def get_student_pop_size(self):
        '''Method to retrieve the number of students

        Returns
        -------
        self.nStudents: :obj:`int`
        '''
        return self.nStudents

    def remove_visitors(self, indices):
        '''Method to remove visitors from the simulation.'''
        for i in indices:
            np.delete(self.population, i)

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
        self.res_houses: :obj:`np.array` of *something* ? not sure yet, this is a work in progress
        '''
        return self.res_houses[self.res_houses != NULL_ID]

    def get_res_size(self):
        '''Method to retrieve the number of students in residence

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

    def count_infected_students(self):
        '''Method to count how many infected students there are.

        Returns
        -------
        infStudents: :obj:`int`
        '''
        infStudents = 0
        for i in range(self.nPop):
            if (self.student_indices[i] != NULL_ID and self.infected[i] != NULL_ID):
                infStudents += 1
        return infStudents

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

    def get_person(self, index):
        '''Method to return an individual based on their index.

        Returns
        -------
        np.population[index]: :obj:`int`
        '''
        return self.population[index]

    def infect(self, index, day):
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
        didWork = self.population[index].infect(day=day)
        if didWork:
            self.infected[index] = index
            self.susceptible[index] = NULL_ID
            if self.population[index].ICU:
                self.ICU[index] = index
            elif self.population[index].hospitalized:
                self.hospitalized[index] = index

        return didWork

    def infect_incoming_students(self, indices, day):
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
            self.infect(index=i, day=day-daysAgo)
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
        if self.infected[index] == index or self.susceptible[index] == -1 or not self.population[index].is_infected():
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
        self.ICU[index] = NULL_ID
        self.dead[index] = index
        return True

    def update_quarantine(self, day):
        '''Method to release everyone who has done their quarantine - DOES NOT ADD NEW PPL TO LIST

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

    def random_symptomatic(self):
        '''Method that causes a random sample of people to develop cold like symptoms.'''
        for person in self.population:
            person.not_infected_symptoms()

    def update_symptomatic(self, day):
        '''Method to add people to the testing waitlist based on their symtoms.

        Parameters
        ----------
        day: int
            The current day the simulation is on.
        '''
        #updates everyone's symptoms
        for i in range (len(self.infected)):
            if self.population[i].check_symptoms(day):

                if i not in self.testing and self.have_been_tested[i] != 1: # if person is not already in testing function
                    infected_person = self.population[i] #gets the infected person from the population list
                    if random.random()/self.population[i].get_protocol_compliance() < self.prob_of_test:
                        if infected_person.show_symptoms and not infected_person.knows_infected:
                            self.testing.append(i) #adds the person to the testing list
                            self.population[i].knows_infected = True
                    elif infected_person.check_test_day(day):
                        self.have_been_tested[i] = 0 #remove them from the testing list (allows them to get retested if they get symptoms again)


    def get_testing_wait_list(self):
        '''Method to return number of people waiting to be tested.

        Returns
        -------
        len(self.testing): :obj:`int`
        '''
        return len(self.testing)

    def get_tested(self, tests_per_day, day):
        '''Method to test people in the testing waitlist.

        Parameters
        ----------
        tests_per_day: int
            Paramter gives the number of tests run.
        day: int
            The day the testing is being done on
        '''
        # if less people are in the list than testing capacity test everyone in the list
        if len(self.testing) < tests_per_day:
            tests_per_day = len(self.testing)
        self.test_sum += tests_per_day # Add the daily tests to the total number of tests

        self.new_quarantined_num = 0 # Reset number of newly quarantined
        num_contacts_traced = 0

        for _ in range(tests_per_day):
            person_index = self.testing[0]  # Gets first person waiting for test
            self.testing.pop(0)   # Removes first person waiting for test
            person = self.population[person_index]
            person.set_test_day(day)
            self.have_been_tested[person_index] = person_index
            if self.ct_enabled and num_contacts_traced < self.ct_capacity:
                person.contact_tracing(day=day)
                num_contacts_traced += 1

            if person.infected:
                person.knows_infected = True
                # quarantines the person
                person.set_quarantine(day)
                self.quarantined[person_index] = person_index
                self.new_quarantined_num += 1
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

    def update_vaccinated(self, day): #needs docstring
        '''Method to add people to the list of vaccinated people

        Parameters
        ----------
        day : int
            The day the testing is being done on.
        '''
        non_vaccinated = []
        for index in range(self.nPop):
            if not self.population[index].is_vaccinated():
                non_vaccinated.append(index) #non-vaccinated list = people who are waiting to get vaccine

        non_vaccinated = np.array(non_vaccinated)
        if len(non_vaccinated)>=self.num_vaccinations:
            self.to_vaccinate = non_vaccinated[np.random.choice(range(len(non_vaccinated)),
                                                                self.num_vaccinations, replace=False).astype(int)]
        else:
            self.to_vaccinate = non_vaccinated[np.random.choice(range(len(non_vaccinated)),
                                                   len(non_vaccinated), replace=False).astype(int)]
        for index in self.to_vaccinate:
            person_to_vaccinate = self.population[index]

            person_to_vaccinate.set_vaccinated(day)
            self.vaccinated[index] = index

            if len(self.to_vaccinate)<self.max_vaccinations:
                break

    def change_mask_wearing(self):
        '''Method to mandate wearing a mask.

        Parameters
        ----------
        has_mask: bool
        '''
        for person in self.population:
            person.has_mask = True
