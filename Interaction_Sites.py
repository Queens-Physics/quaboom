from cv19 import Person
from cv19 import Population
import random
import numpy as np


class Interaction_Sites:

    def __init__(self, population, houses_per_neighbourhood,nDays):

        self.population = population  # list of all people
        self.house_list = self.population.household  # list of all households
        house_number = len(self.house_list) # number of houses
        neighbourhood_number = int(house_number / houses_per_neighbourhood) # number of neighbourhoods
        self.neighbourhoods = [] # list of all houses's neighbourhood index
        self.nDays = nDays #number of days past

        # creates neighbourhoods
        for i in range(house_number):
            neighbourhood_index = random.randint(0, neighbourhood_number) #creates a neighbourhood index for each house
            self.neighbourhoods.append(neighbourhood_index) #adds the neighbourhoods index to the neighbourhood list

    # creates workplaces
    def work_init (self,job_type,avg_office_size,office_size_distrubution):
        self.industry = [] #all people in a specific industry
        self.office_sizes = [] # list of the sizes of each office
        self.office_places = [] #list of the workplace the person is at
        population_size = len(self.population) # size of the population
        # adds all people of the same job to an office place
        for i in range (population_size):
            if (obj.get_job == job_type for obj in self.population[i]):
                self.industry.append(self.population[i]) #adds each person to a list of all people at the industry
                nOffices = int(population_size/avg_office_size) #creates a number of offices
                self.office_places.append(random.randint(1, nOffices)) #chooses a random office for each person to go to

    #goes through a work space and generates a list of all people there
    def work (self,job_type,workplace_index):
        work_place = []
        for i in range (len(self.industry)):
            if (obj.get_job == job_type for obj in self.industry[i]) and (self.office_places[i] == workplace_index):
                 work_place.append(self.industry[i])
        return work_place


    # common location function
    def standard_location(self,population_size,neighbourhood_range):
        local_people = []
        rand_list_people = []
        public_pop = 0
        #creates a list of people from the neighbourhoods in the range given
        for p in range (len(neighbourhood_range)):
            public_pop += neighbourhood_range[p]
        for q in range (self.neighbourhoods):
            if self.neighbourhoods[q] <= neighbourhood_range[1] or self.neighbourhoods[q] >= neighbourhood_range[0]:
                rand_list_people.append(random.randint(0,int(public_pop/population_size)))
        #choose random people from the neibourhood to interact with
        for i in range (self.neighbourhoods):
            if self.neighbourhoods[i] <= neighbourhood_range[1] or self.neighbourhoods[i] >= neighbourhood_range[0]:
                if rand_list_people[i] == population_size:
                    local_people.append(self.population.check_individual[i])

        return local_people

    #creates a list of all people going to the grocery store
    def grocery_store_init(self,neighbourhood_number,grocery_store_number_per_neighbourhood):

        neighbourhood = []
        self.grocery_stores_list_of_people = []
        self.which_grocery_store = []
        for q in range(len(self.neighbourhoods)):
            if self.neighbourhoods[q] == neighbourhood_number:
                neighbourhood.append(self.house_list[q])
                self.which_grocery_store.append(random.randint(0, grocery_store_number_per_neighbourhood))

        for i in range(len(neighbourhood)):
            house_length = len(neighbourhood[i])
            person_index = random.randint(0, house_length)

            # find a better way to do this so no infinite loop occurs or find a better way to create the houses
            if (neighbourhood[i][person_index].get_age() != '0-9'):
                self.grocery_stores_list_of_people.append(neighbourhood[i][person_index])
            else:
                i -= 1

    def grocery_store(self, grocery_store_index):

        grocery_store_population = [] # list of people at the grocery store

        for i in range(0, self.number_grocery_stores):
            # goes through everyone who has the grocery store as their index and adds them to a list
            if self.which_grocery_store[i] == grocery_store_index:
                grocery_store_population.append(self.grocery_stores_list_of_people[i])
        return grocery_store_population

    # home
    def home (self,house_index):
        resident_list =  self.population.household(house_index) #list of residents in a house
        resident_list_index = []
        infected_house = False
        for i in range (len(resident_list)):
            resident_list_index.append(resident_list[i].get_index()) #gets the index of each person in the house
            #if anyone in the house is infected the house is infected
            if (obj.is_infected() == True for obj in resident_list[i]):
                infected_house = True
        #infect everyone in the house
        if (infected_house == True):
            for i in range (len(resident_list)):
                if (obj.is_infected() == False for obj in resident_list[i]):
                    person = self.population.check_individual(resident_list_index[i]).infect(self.nDays)
                    self.population.update_infected(person.get_index())


    # interaction function
    def will_interaction(self, local_population, size_of_location,contact_matrix,busyness):
        interaction_list = []
        for i in range(len(local_population)):
            # get variables of people from local population
            person = local_population[i]
            isolation_tend = person.isolation_tendencies
            placeholder_equation = size_of_location*contact_matrix*busyness*isolation_tend
            potential_interaction_number = 2  # will be calculated by a bunch of variables that I do not know
            interaction_number = random.randint(0, potential_interaction_number)
            interaction_list.append(interaction_number)
        return interaction_list

    # determines who will interact with who
    def who_will_interact(self, interaction_list, local_population):
        interactions = [] # list of all interaction
        for i in range (len(local_population)):
            person_interactions = [] # list of each person's index person i interacts with
            interaction_number = interaction_list[i]
            for j in range (interaction_number):
                interaction_index = random.randint(0,len(local_population)) #chooses a random person in the list to interact with
                if (interaction_list[interaction_index] > 0):
                    interaction_list[interaction_index] -= 1 #removes an interaction from that persons possible interactions
                    person_interactions.append(interaction_index) #adds that person to their interaction
                else:
                    #potential infinite loop
                    j-= 1
                interactions.append(person_interactions)
        return interactions

    # probability of the virus spreading based on the interactions in the who will interact function
    def prob_of_spread(self,local_population, who_will_interact):

        for i in range (len(local_population)):
            infection_probability = [] # probability of infection for each person
            interactions = who_will_interact[i] # number of interactions person i had
            for j in range (len(interactions)):
                index = interactions[j] # person j's index
                person = local_population[index] #gets person j
                if (person.is_infected() == True):
                    #gathers data from person
                    prob_of_infection = 0.1 # using info from person
                    infection_probability.append(prob_of_infection) #adds the probability of infection to a list
            prob = sum(infection_probability) #sums all the infection probabilities
            #produces a random number which if within the probability bounds infects the person
            if random.random()  <= prob:
                local_population[i].infect(self.nDays) #infects the person
                self.population.update_infected(i)  # update the list of suceptiple and infected people