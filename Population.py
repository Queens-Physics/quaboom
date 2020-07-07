import numpy as np
import random
import Person

class Population:
    '''creates a population of people based on the total population
     uses and age distrubution to weight the assignment of ages'''

    def __init__(self, nPop, n0, ageDistrubution, jobDistrubution, householdDistribution, isolationArray):

        self.people = []  # The list of all people
        self.suceptible = [] #list of all suceptible individuals
        self.infected = []  # list of all infected people
        self.recovered = [] # list of recovered people
        self.household = [] #list of all houses (list that contains all lists of the people in the house)
        self.pop = nPop #total population 

        for i in range(0, self.pop):

            #age distrubution
            Age = (['0-9'] * ageDistrubution[0] + ['10-19'] * ageDistrubution[1]
                   + ['20-29'] * ageDistrubution[2] + ['30-39'] * ageDistrubution[3]
                   + ['40-49'] * ageDistrubution[4] + ['50-59'] * ageDistrubution[5]
                   + ['60-69'] * ageDistrubution[5] + ['70-79'] * ageDistrubution[6]
                   + ['80-89'] * ageDistrubution[7] + ['90+'] * ageDistrubution[8])
            #selects an age based on the age distrubution
            age = random.choice(Age)


            #determines the isolation tendancy based on age
            if age == '0-9':
                isolation_tendencies = isolationArray[0]
            elif age == '10-19':
                isolation_tendencies = isolationArray[1]
            elif age == '20-29':
                isolation_tendencies = isolationArray[2]
            elif age == '30-39':
                isolation_tendencies = isolationArray[3]
            elif age == '40-49':
                isolation_tendencies = isolationArray[4]
            elif age == '50-59':
                isolation_tendencies = isolationArray[5]
            elif age == '60-69':
                isolation_tendencies = isolationArray[6]
            elif age == '70-79':
                isolation_tendencies = isolationArray[7]
            elif age == '80-89':
                isolation_tendencies = isolationArray[8]
            elif age == '90+':
                isolation_tendencies = isolationArray[9]
            else:
                isolation_tendencies = 1

            Job = ['Essential'] * jobDistrubution[0] + ['Commercial'] * jobDistrubution[1]

            #creates a new person
            NewPerson = Person(index=i, infected=False, recovered=False,infected_day=None, recovered_day=None,
                        others_infected=None, cure_days=None, recent_infections=None, age, Job, House_index=0,isolation_tendencies)
            self.people.append(NewPerson)  # adds new person to list

            # Creation of the households
            house_number = 0 # the number of houses is 0
            temporaryPopulationList = len(self.people)  # creates a temporary list
            for i in range(0, len(self.people)):
                houseList = [] # creates a list of all people in a house
                if (temporaryPopulationList > 0):
                    HousePopProb = (['1'] * householdDistribution[0] + ['2'] * householdDistribution[1]
                                    + ['3'] * householdDistribution[2] + ['4'] * householdDistribution[3] + ['5'] *
                                    householdDistribution[4]+ ['6'] * householdDistribution[5])
                    HousePop = int(random.choice(HousePopProb)) # calculates the number of people in the house

                    for f in range(0, HousePop):
                        if (temporaryPopulationList > 0):
                            self.people[i].set_house(house_number) #sets person i into house n
                            houseList.append(self.people[i]) #adds person to that house list
                            temporaryPopulationList = temporaryPopulationList - 1  #removes them from the temporary list length
                            self.household.append(houseList)  # adds the house to the total list of all houses
                    house_number = house_number + 1

        # infects the initial people
        self.suceptible = self.people
        for i in range(n0):
            self.people[i].infect(day=0)
            self.infected.append(self.people[i])
            self.suceptible.pop(i)
    
    #returns the population
    def get_population(self):
        return self.nPop

    # counts the total number of suceptible individuals
    def count_suceptible(self):
        suceptiple_population = len(self.suceptible)
        return suceptiple_population

    #returns an individual based on their index
    def check_individual(self, index):
        return self.people[index]

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
        for i in range (len(self.infected):
            if (obj.is_infected == False for obj in self.infected):
                self.recovered.append(self.suceptible[i])
                self.infected.pop(i)
        return self.recovered

    #returns the total number of houses
    def check_num_house(self):
        Set = set(obj.household for obj in self.people)
        sum = len(Set)
        return sum

    # returns all people in a specific house
    def get_house(self, index):
        return self.household[index]

