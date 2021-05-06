import numpy as np
import Person
import json
import random

json_file = open('dataK.json')
disease_params = json.load(json_file)


AGE_OPTIONS = ['0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+']
JOB_OPTIONS = ['Health', 'Sales', 'Neither']
HOUSE_OPTIONS = [1,2,3,4,5]
ISOLATION_OPTIONS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
SEVERITY_OPTIONS = ['Mild', 'Hospitalization', 'ICU', 'Death']
MASK_OPTIONS = ['Surgical', 'Non-surgical']

# isolation #
ISOLATION_WEIGHTS = np.ones(len(ISOLATION_OPTIONS))
# Normalize the probability
ISOLATION_WEIGHTS /= float(sum(ISOLATION_WEIGHTS)) #this is the one we don't have data on yet

# PULL DATA FROM THE JSON FILE #
# age #
AGE_WEIGHTS = np.zeros(len(AGE_OPTIONS))
for iage in range (len(AGE_WEIGHTS)):
    string = str(iage*10)+'-'+str(iage*10+9)
    AGE_WEIGHTS[iage]= disease_params['age_weights'][0][string]

# job #
JOB_WEIGHTS = np.zeros(len(JOB_OPTIONS))
for ijob in range (len(JOB_WEIGHTS)):
    string = JOB_OPTIONS[ijob].upper()
    JOB_WEIGHTS[ijob]= disease_params['job_weights'][0][string]


# house # 
HOUSE_WEIGHTS = np.zeros(len(HOUSE_OPTIONS))
for ihouse in range (len(HOUSE_WEIGHTS)):
    string = str(ihouse+1)
    HOUSE_WEIGHTS[ihouse]= disease_params['house_weights'][0][string]

# case severity #
SEVERITY_WEIGHTS = np.zeros(len(SEVERITY_OPTIONS))
for iseverity in range (len(SEVERITY_WEIGHTS)):
    string = SEVERITY_OPTIONS[iseverity]
    SEVERITY_WEIGHTS[iseverity]= disease_params['case_severity'][0][string]

# mask type #
MASK_WEIGHTS = np.zeros(len(MASK_OPTIONS))
for imask in range (len(MASK_WEIGHTS)):
    string = MASK_OPTIONS[imask]
    MASK_WEIGHTS[imask]= disease_params['mask_type'][0][string]
    
# mask
PROB_HAS_MASK = 0.8

json_file.close()

NULL_ID = -1 # This value means that the person index at this location is not susceptible/infected/dead/...
             # All arrays are intialized to this (except healthy, as everyone is healthy)


PROB_OF_TEST = 1 #probability that the person will get tested

# Capacity for contact tracing daily
CT_CAPACITY = 10000
CT_ENABLED = True

class Population:
    '''creates a population of people based on the total population
     uses and age distrubution to weight the assignment of ages

     suscept list has negative values for infected, and positive indicies for susept
     infected list has negative values for healthy, and positive indicies for infected
     recovered list has negative values for not recovered, and postitive indicies for recovered
     '''

    def __init__(self, nPop, n0, policy):

        self.policy = policy

        self.population = [0] * nPop  # The list of all people
        self.household = [0] * nPop # list of all houses (list that contains all lists of the people in the house)
        self.nPop = nPop # total population

        houseSize = np.random.choice(a=HOUSE_OPTIONS, p=HOUSE_WEIGHTS)
        houseIndex = 0
        self.household[houseIndex] = houseSize

        # Student parameter
        nStudents = int(nPop/5) # full capacity ~ 24k students
        
        # Initialize parameters of people immediately.
        # Much quick this way, utilizes numpy efficiency.
        age_arr = np.random.choice(a=AGE_OPTIONS, p=AGE_WEIGHTS, size=nPop)
        job_arr = np.random.choice(a=JOB_OPTIONS, p=JOB_WEIGHTS, size=nPop)
        isolation_tend_arr = np.random.choice(a=ISOLATION_OPTIONS, p=ISOLATION_WEIGHTS, size=nPop)
        case_severity_arr = np.random.choice(a=SEVERITY_OPTIONS, p=SEVERITY_WEIGHTS, size=nPop)
        mask_type_arr = np.random.choice(a=MASK_OPTIONS, p=MASK_WEIGHTS, size=nPop)
        has_mask_arr = np.random.uniform(size=nPop) < PROB_HAS_MASK

        for i in range(0, nPop-nStudents):
            # MAKE A PERSON
            newPerson = Person.Person(index=i, infected=False, recovered=False, dead=False, hospitalized=False,
                                      quarantined=False, quarantined_day=None,
                                      infected_day=None, recovered_day=None, death_day=None,
                                      others_infected=None, cure_days=None, recent_infections=None,
                                      age=age_arr[i], job=job_arr[i], house_index=0,
                                      isolation_tendencies=isolation_tend_arr[i],
                                      case_severity=case_severity_arr[i], mask_type=mask_type_arr[i], 
                                      has_mask=has_mask_arr[i])

            # ADD A PERSON
            self.population[i] = newPerson

            # Increment house info
            houseSize -= 1
            if houseSize == 0:
                houseSize = np.random.choice(HOUSE_OPTIONS)
                houseIndex += 1
                self.household[houseIndex] = houseSize
                
        ############### STUDENTS ###############
        self.students = np.zeros(nPop, dtype=int) + NULL_ID # list of people who are students

        for i in range(nPop-nStudents, nPop):
            student_age = random.randint(18,23)
            newStudent = Person.Person(index=i, infected=False, recovered=False, dead=False, quarantined=False, 
                               quarantined_day=None, infected_day=None, recovered_day=None, death_day=None,
                               others_infected=None, cure_days=None, recent_infections=None, age=student_age, job='Student',
                               house_index=0, isolation_tendencies=isolation_tend_arr[i],
                               case_severity=case_severity_arr[i], has_mask=has_mask_arr[i])
            self.population[i] = newStudent

            self.students[i] = i # set their student status
            

        # Make sure last household number is right (when it runs out of people to fill)
        if houseSize != self.household[houseIndex]:
            self.household[houseIndex] = houseSize

        # Slice household list to the right size
        self.household = self.household[:houseIndex]

        # Create person status arrays
        self.susceptible = np.array(range(nPop), dtype=int)         # list of all susceptible individuals
        self.infected = np.zeros(nPop, dtype=int) + NULL_ID         # list of all infected people
        self.recovered = np.zeros(nPop, dtype=int) + NULL_ID        # list of recovered people
        self.dead = np.zeros(nPop, dtype=int) + NULL_ID             # list of recovered people
        self.hospitalized = np.zeros(nPop, dtype=int) + NULL_ID     # list of people hospitalized and in the ICU
        self.have_been_tested = np.zeros(nPop, dtype=int) + NULL_ID # list of people who have been tested
        self.knows_infected = np.zeros(nPop, dtype=int) + NULL_ID   # list of people who have a positive test and are still infected
        self.quarantined = np.zeros(nPop, dtype=int) + NULL_ID      # list of people who are currently in quarantine

        self.testing = [] # list of people waiting to be others_infected
        self.test_sum = 0 # total number of tests that have been run
        self.quarantined_sum = 0 # total number of people in quarantine (created as the list was having indexing issues)

        # Select the indices of the n0 initially infected people
        # randomly, and then infect them
        indices = random.sample(range(nPop), n0)
        for i in indices:
            self.population[i].infect(day=0)
            self.infected[i] = i
            self.susceptible[i] = NULL_ID

        self.new_quarantined_num = 0

    #returns the population
    def get_population_size(self):
        return self.nPop

    def get_population(self):
        return self.population
    
    def remove_visitors(self, indices):
        for i in indices:
            np.delete(self.population, i)

    # Properly return the actual indices of each bin of people
    def get_susceptible(self):
        return self.susceptible[self.susceptible != NULL_ID]
    
    def get_infected(self):
        return self.infected[self.infected != NULL_ID]
    
    def get_recovered(self):
        return self.recovered[self.recovered != NULL_ID]
    
    def get_dead(self):
        return self.dead[self.dead != NULL_ID]
    
    def get_hospitalized(self):
        return self.hospitalized[self.hospitalized != NULL_ID]
    
    def get_quarantined(self):
        return self.quarantined[self.quarantined != NULL_ID]
    
    def get_students(self): # change this to look thru job == 'Student' ?
        return self.students[self.students != NULL_ID]
    
    # Count the number of people in each bin
    def count_susceptible(self):
        return np.count_nonzero(self.susceptible != NULL_ID)
    
    def count_infected(self):
        return np.count_nonzero(self.infected != NULL_ID)
    
    def count_infected_students(self):
        infStudents = 0
        for i in range (self.nPop):
            if (self.students[i] != NULL_ID and self.infected[i] != NULL_ID):
                infStudents += 1
        return infStudents
    
    def count_recovered(self):
        return np.count_nonzero(self.recovered != NULL_ID)

    def count_dead(self):
        return np.count_nonzero(self.dead != NULL_ID)
    
    def count_hospitalized(self):
        return np.count_nonzero(self.hospitalized != NULL_ID)
    
    def count_quarantined(self):
        return np.count_nonzero(self.quarantined != NULL_ID)
    
    def count_masks(self):
        return np.count_nonzero(self.has_mask > 0)
    
    #returns an individual based on their index
    def get_person(self, index) -> Person:
        return self.population[index]

    # Infect a person
    def infect(self, index, day):
        didWork = self.population[index].infect(day=day)
        if didWork:
            self.infected[index] = index
            self.susceptible[index] = NULL_ID
            if self.population[index].hospitalized:
                self.hospitalized[index] = index
    
        return didWork

    # Update lists for already infected people
    def update_infected(self, index):
        if self.infected[index] == index or self.susceptible[index]==-1 or self.population[index].is_infected()==False:
            # Already infected, or cant be infected
            return False
        self.infected[index] = index
        self.susceptible[index] = NULL_ID
        return True

    # Cure a person
    def cure(self, index, day):
        didWork = self.population[index].check_cured(day)
        if didWork:
            self.infected[index] = NULL_ID
            self.recovered[index] = index
        return didWork

    # Updates lists for already cured people
    def update_cured(self, index):
        if self.recovered[index]==index or self.population[index].is_recovered()==False:
            # Already recovered in pop obj or person obj is not actually recovered
            return False
        self.infected[index] = NULL_ID
        self.recovered[index] = index
        self.hospitalized[index] = NULL_ID
        return True

    def die(self, index, day):
        didWork = self.population[index].check_dead(day)
        if didWork:
            self.infected[index] = NULL_ID
            self.recovered[index] = NULL_ID
            self.dead[index] = index
        return didWork

    def update_dead(self, index):
        if self.dead[index]==index or self.population[index].is_dead()==False:
            return False
        self.infected[index] = NULL_ID
        self.recovered[index] = NULL_ID
        self.hospitalized[index] = NULL_ID
        self.dead[index] = index
        return True

    def update_quarantine(self, day):
        # Release everyone who has done their quarantine - DOES NOT ADD NEW PPL TO LIST
        for i in self.get_quarantined():
            # Check their status
            if self.population[i].leave_quarantine(day) == True:
                self.quarantined[i] = NULL_ID

    def count_quarantined(self):
        return np.count_nonzero(self.quarantined != NULL_ID) 
    
    def get_new_quarantined(self):
            return self.new_quarantined_num
        
    def count_tested(self):
        return self.test_sum

    #causes random people to get the cold                    
    def random_symptomatic(self): 
        for i in range (len(self.population)):
            self.population[i].not_infected_symptoms()

    # updates the list of symptomatic people and adds the people who are symtomatic to the testing array
    def update_symptomatic(self, day):

        #updates everyone's symptoms
        for i in range (len(self.infected)):
            if self.population[i].check_symptoms(day)==True:

                if i not in self.testing and self.have_been_tested[i]!=1: # if person is not already in testing function
                    if random.random() < PROB_OF_TEST:
                        infected_person = self.population[i] #gets the infected person from the population list

                        if infected_person.show_symptoms==True and infected_person.knows_infected==False:
                            self.testing.append(i)#adds the person to the testing list
                            self.population[i].knows_infected = True
    
    
    def get_testing_wait_list(self): 
        return len(self.testing)
    
    def get_tested(self, tests_per_day, day):
        
        #if less people are in the list than testing capacity test everyone in the list
        if len(self.testing) < tests_per_day:
            tests_per_day = len(self.testing)
        self.test_sum += tests_per_day # add the daily tests to the total number of tests
        
        self.new_quarantined_num = 0 # reset number of newly quarantined
        
        # Number of contacts traced so far
        num_contacts_traced = 0

        for i in range(tests_per_day):
            person_index = self.testing[0] #gets first person waiting for test
            self.testing.pop(0) # removes first person waiting for test
            person = self.population[person_index]

            if person.infected == True:
                person.knows_infected = True
                #quarantines the person
                person.set_quarantine(day)
                self.quarantined[person_index] = person_index
                self.have_been_tested[person_index] = person_index

                # Contact trace the person
                if CT_ENABLED and num_contacts_traced < CT_CAPACITY:
                    person.contact_tracing(day)
                    num_contacts_traced += 1


                self.new_quarantined_num += 1
            else:
                person.knows_infected = False
                self.have_been_tested[person_index] = person_index

