import numpy as np
import random
import Person
import copy as copy

AGE_OPTIONS = ['0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+']
JOB_OPTIONS = ['Essential', 'Commercial']
HOUSE_OPTIONS = [1,2,3,4,5,6]
ISOLATION_OPTIONS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

AGE_WEIGHTS = np.ones(len(AGE_OPTIONS))
JOB_WEIGHTS = np.ones(len(JOB_OPTIONS))
HOUSE_WEIGHTS = np.ones(len(HOUSE_OPTIONS))
ISOLATION_WEIGHTS = np.ones(len(ISOLATION_OPTIONS))


class Population:
    '''creates a population of people based on the total population
     uses and age distrubution to weight the assignment of ages
     
     suscept list has negative values for infected, and positive indicies for susept
     infected list has negative values for healthy, and positive indicies for infected
     recovered list has negative values for not recovered, and postitive indicies for recovered
     '''

    def __init__(self, nPop, n0):

        self.population = [0]*nPop  # The list of all people
        self.household = [0]*nPop #list of all houses (list that contains all lists of the people in the house)
        self.pop = nPop #total population 
        
        houseSize = np.random.choice(a=HOUSE_OPTIONS, p=HOUSE_WEIGHTS)
        houseIndex = 0
        self.household[houseIndex] = houseSize

        for i in range(0, self.pop):
            # MAKE A PERSON
            age = np.random.choice(a=AGE_OPTIONS, p=AGE_WEIGHTS)
            job = np.random.choice(a=jobOptions, p=jobWeights)
            isolation_tend = np.random.choice(a=ISOLATION_OPTIONS, p=ISOLATION_WEIGHTS)

            newPerson = Person(index=i, infected=False, recovered=False, infected_day=None, recovered_day=None, 
                               others_infected=None, cure_days=None, recent_infections=None, age=age, 
                               job=job, house_index=0,isolation_tendencies=isolation_tendencies)
            
            # ADD A PERSON
            self.population[i] = newPerson
            
            # Increment house info
            houseSize -= 1
            if houseSize == 0:
                houseSize = np.random.choice(HOUSE_OPTIONS)
                houseIndex += 1
                self.household[houseIndex] = houseSize
                
        # Make sure last household number is right (when it runs out of people to fill
        if houseSize != self.household[houseIndex]:
            self.household[houseIndex] = houseSize
            
        # Slice household list to the right size
        self.household = self.household[:houseIndex]
        
        # Create person status arrays
        self.suceptible = np.array(range(nPop)) #list of all suceptible individuals
        self.infected = np.zeros(nPop) - 1  # list of all infected people (all healthy (negative) to start)
        self.recovered = np.zeros(nPop) - 1 # list of recovered people (all not recovered (negative) to start)
        
        # Infect first n0 people
        for i in range(n0):
            self.population[i].infect(day=0)
            self.infected[i] = i
            self.suceptible[i] = -1
    
    #returns the population
    def get_population_size(self):
        return self.nPop

    # Properly return the actual indices of each bin of people
    def get_suceptible(self):
        return copy.deepcopy(self.suceptible[self.suceptible > 0])
    
    def get_infected(self):
        return copy.deepcopy(self.infected[self.infected > 0])
    
    def get_recovered(self):
        return copy.deepcopy(self.recovered[self.recovered > 0])
    
    # Count the number of people in each bin
    def count_suceptible(self):
        return len(self.get_susceptible)
    
    def count_infected(self):
        return len(self.get_infected)
    
    def count_recovered(self):
        return len(self.get_recovered)

    #returns an individual based on their index
    def get_person(self, index):
        return self.population[index]
    
    # Infect a certain individual
    def infect(self, index, day):
        didWork = self.population[i].infect(day=day)
        if didWork:
            self.infected[i] = i
            self.suceptible[i] = -1
        
        return didWork
    
    # returns the list of suceptible  individuals
    def check_suceptible(self):
        for i in range(len(self.suceptible)):
            if (obj.is_infected == True for obj in self.suceptible):
                self.infected.append(self.suceptible[i])
                self.suceptible.pop(i)
        return self.suceptible

    # counts the total number of infected individuals
    def count_infected(self):
        infected_population = len(self.infected)
        return infected_population

    # returns the list of infected individuals
    def check_infected(self):
        for i in range(len(self.suceptible)):
            if (obj.is_infected == True for obj in self.suceptible):
                self.infected.append(self.suceptible[i])
                self.suceptible.pop(i)
        return self.infected

    # counts the total number of recovered individuals
    def count_recovered(self):
        recovered_population = len(self.recovered)
        return recovered_population

    #returns a list of all people recovered
    def check_recovered(self):
        for i in range(len(self.infected)):
            if (obj.is_infected == False for obj in self.infected):
                self.recovered.append(self.suceptible[i])
                self.infected.pop(i)
        return self.recovered

    #returns the total number of houses
    def check_num_house(self):
        house_sum = len(set(obj.household for obj in self.people))
        return house_sum

    # returns all people in a specific house
    def get_house(self, house_index):
        return self.household[house_index]

    
    1543 Ultrabar Marryville