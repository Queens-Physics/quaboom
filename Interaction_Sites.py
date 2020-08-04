import Person
import Population
import random
import numpy as np

# __init__ parameters
GRADE_A_PER_POP = 1./500
GRADE_B_PER_POP = 1./500
GRADE_C_PER_POP = 1./500

A_LOYALTY_MEAN, A_LOYALTY_STD = 4, 2
B_LOYALTY_MEAN, B_LOYALTY_STD = 1, 1
C_LOYALTY_MEAN, C_LOYALTY_STD = 1, .5

# Infection spread parameters
INFECTION_SPREAD_PROB = 0.3

# House spread parameters
HOUSE_SPREAD_PROB = 0.2

class Interaction_Sites:
    
    ###### NEW CLASS ######
    def __init__(self, pop_obj):
        
        # Grade A means ones you go to different ones of (resturants, gas station, retail stores)
        # Grade B means usually the same one, but sometimes not (gym, grocery store)
        # Grade C means almost always go to the same one (office, school)

        # Generates a list of ppl that go to different grade X sites
        # len(grade_X_sites) is how many sites there are; len(grade_X_sites[i]) is how many ppl go to that site
        
        self.grade_A_sites = np.array(self.init_grade(pop_obj, GRADE_A_PER_POP, A_LOYALTY_MEAN, A_LOYALTY_STD))
        self.grade_B_sites = np.array(self.init_grade(pop_obj, GRADE_B_PER_POP, B_LOYALTY_MEAN, B_LOYALTY_STD))
        self.grade_C_sites = np.array(self.init_grade(pop_obj, GRADE_C_PER_POP, C_LOYALTY_MEAN, C_LOYALTY_STD))
        self.house_sites = np.array(pop_obj.household).copy()
        
        
    def init_grade(self, pop_obj, grade_pop_size, loyalty_mean, loyalty_std):
        # Find out how many sites there should be - guessing right now 
        num_sites = round(pop_obj.get_population_size()*grade_pop_size)
        grade_sites = [[] for i in range(num_sites)]
        
        for person in pop_obj.get_population():
            # Assign people to this specific site
            num_diff_sites = round(np.random.normal(loyalty_mean, loyalty_std))
            
            # Get a list of len num_diff_sites for this person to be associated with now
            person_sites = np.random.choice(num_sites, num_diff_sites, replace=False)
            for site in person_sites:
                # Assign this person to that site
                grade_sites[site].append(person.get_index())
                
        # Convert everything to numpy arrays
        for i, site in enumerate(grade_sites):
            grade_sites[i] = np.array(site)
                
        return grade_sites
                
        
    def will_visit_site(self, site_array, will_go_prob):
        # Function that finds how many people will go to each site of a grade in a given day
        # Returns a list of true or false of size(self.grade_X_sites) that has true for ppl going that day
        
        # Could add something here that limits how many sites one person can visit (not real to visit 11 sites a day)
        will_visit_grade = [[] for i in range(len(site_array))]
        for i, site in enumerate(site_array):
            site_attendance = np.array([random.random()<will_go_prob for person in site])
            will_visit_grade[i] = site[site_attendance==True]

        return will_visit_grade
    
    
    def site_interaction(self, pop_obj, will_go_array, site_array, day):
        # Find out how many interactions each person has at the site - FUNCTION IS PRETTY SLOW RN
        # Should deal with case where one person is left with more than one interaction
        new_infections = np.zeros(pop_obj.get_population_size(), dtype=int)
        new_infections_count = 0
        
        for ppl_going in will_go_array:
            
            infected_persons = [index for index in ppl_going if pop_obj.get_person(index).is_infected()==True]
            recovered_persons = [index for index in ppl_going if pop_obj.get_person(index).is_recovered()==True]
            
            if len(infected_persons)==0 or len(infected_persons)+len(recovered_persons)==len(ppl_going):
                continue # No ppl to infect here or no one already infected
            
            # Generate a list of how many interactions ppl have at the site
            num_interactions = np.array([self.calc_interactions(pop_obj, person_index, len(ppl_going)) 
                                         for person_index in ppl_going])
            
            while np.sum(num_interactions > 0) > 1:
                # grab the highest interactor
                person_1 = np.argmax(num_interactions)
                # find a random interactor for them to pair with (that is not them)
                new_options = [i for i in range(len(num_interactions)) if num_interactions[i] > 0 and i != person_1]
                person_2 = np.random.choice(new_options)
                    
                # Get the actual people at these indexes
                person_1_index = ppl_going[person_1]
                person_2_index = ppl_going[person_2]
                
                # Have an interaction between those people
                did_infect = self.interact(pop_obj, person_1_index, person_2_index)
                if did_infect:
                    person_1_infected = pop_obj.get_person(person_1_index).is_infected()
                    new_infections[new_infections_count] = person_2_index if person_1_infected else person_1_index
                    new_infections_count += 1
                
                # Lower the interaction count for those people
                num_interactions[person_1] -= 1
                num_interactions[person_2] -= 1
                
            
        # Update people who get infected only at the end (if i get CV19 at work, prolly wont spread at the store that night ?)
        for new_infection in new_infections[:new_infections_count]:
            pop_obj.infect(index=new_infection, day=day)
           
        
    def calc_interactions(self, pop_obj, person_index, how_busy):
        # This will be some function that returns how many interactions for this person
        upper_interaction_bound = 10
        lower_interaction_bound = 0  # Random numbers at the moment
        
        return np.random.randint(lower_interaction_bound, upper_interaction_bound)
         
        
    def interact(self, pop_obj, person_1, person_2):
        # Function that models the interaction between two people, and will return if interaction spread
        
        # Make sure at least and only one is infected for this to happen
        if pop_obj.get_person(person_1).is_infected() == pop_obj.get_person(person_2).is_infected():
            return False
        elif random.random() < INFECTION_SPREAD_PROB:
            return True
        else:
            return False
    
    
    def house_interact(self, pop_obj, day):
        # It is assumed that if people go to the same home they will interact with eachother
        house_count = 0
        for i in range(len(self.house_sites)):
            # Get ppl in house
            house_size = self.house_sites[i]
            housemembers = pop_obj.get_population()[house_count:house_count+house_size]
            house_count += house_size
            
            # Check if anyone in the house is infected
            infected_housemembers = [i for i in range(house_size) if housemembers[i].is_infected() == True]
            
            if len(infected_housemembers)>0:
                healthy_housemembers = [i for i in range(house_size) if housemembers[i].is_infected() == False]
                
                for person in healthy_housemembers:
                    # This should be more complicated and depend on len(infectpplinhouse)
                    infection_chance = HOUSE_SPREAD_PROB 
                    caught_infection = random.random()<infection_chance
                    if caught_infection:
                        pop_obj.infect(index=housemembers[person].get_index(), day=day)

                        
    def get_grade_A_sites(self):
        return self.grade_A_sites.copy()
    
    def get_grade_B_sites(self):
        return self.grade_B_sites.copy()
    
    def get_grade_C_sites(self):
        return self.grade_C_sites.copy()
                        
                        
# NEXT STEPS HERE: 
# Create a mini-sim to test this code
# use Rys code to fill in the interaction and infection functions
    
    
    
    ################################################## OLD CLASS ##################################################
#     def __init__(self, population, houses_per_neighbourhood, nDays):

#         self.population = population  # list of all people
#         self.house_list = self.population.household  # list of all households
#         neighbourhood_number = int(len(self.house_list) / houses_per_neighbourhood) # number of neighbourhoods
#         self.nDays = nDays # number of days past

#         # creates neighbourhoods
#         self.neighbourhoods = [] # list of all houses's neighbourhood index - one index for each house
#         for i in range(house_number):
#             neighbourhood_index = random.randint(0, neighbourhood_number) # creates a neighbourhood index for each house
#             self.neighbourhoods.append(neighbourhood_index) # adds the neighbourhoods index to the neighbourhood list

#     # Create all workplaces for a specific industry
#     def work_init(self, job_type, avg_office_size, office_size_distrubution):
#         self.industry = []                          # List opf people in this industry
#         self.office_sizes = []                      # List of the sizes of each office
#         self.office_places = []                     # List of the workplace the person is at
#         population_size = len(self.population)
        
#         nOffices = int(population_size/avg_office_size) #creates a number of offices
#         # adds all people of the same job to an office place
#         for i in range (population_size):
#             if (obj.get_job == job_type for obj in self.population[i]):
#                 self.industry.append(self.population[i])              #adds each person to a list of all people at the industry
#                 self.office_places.append(random.randint(1, nOffices))#chooses a random office for each person to go to

#     #goes through a work space and generates a list of all people there
#     def work(self,job_type,workplace_index):
#         work_place = []
#         for i in range(len(self.industry)):
#             if (obj.get_job == job_type for obj in self.industry[i]) and (self.office_places[i] == workplace_index):
#                  work_place.append(self.industry[i])
#         return work_place


#     # common location function
#     def standard_location(self, population_size, neighbourhood_range):
#         local_people = []
#         rand_list_people = []
#         public_pop = 0
#         #creates a list of people from the neighbourhoods in the range given
#         for p in range (len(neighbourhood_range)):
#             public_pop += neighbourhood_range[p]
            
#         for q in range (self.neighbourhoods):
#             if self.neighbourhoods[q] <= neighbourhood_range[1] or self.neighbourhoods[q] >= neighbourhood_range[0]:
#                 rand_list_people.append(random.randint(0,int(public_pop/population_size)))
                
#         #choose random people from the neibourhood to interact with
#         for i in range (self.neighbourhoods):
#             if self.neighbourhoods[i] <= neighbourhood_range[1] or self.neighbourhoods[i] >= neighbourhood_range[0]:
#                 if rand_list_people[i] == population_size:
#                     local_people.append(self.population.check_individual[i])

#         return local_people

#     #creates a list of all people going to the grocery store
#     def grocery_store_init(self,neighbourhood_number,grocery_store_number_per_neighbourhood):

#         neighbourhood = []
#         self.grocery_stores_list_of_people = []
#         self.which_grocery_store = []
#         for q in range(len(self.neighbourhoods)):
#             if self.neighbourhoods[q] == neighbourhood_number:
#                 neighbourhood.append(self.house_list[q])
#                 self.which_grocery_store.append(random.randint(0, grocery_store_number_per_neighbourhood))

#         for i in range(len(neighbourhood)):
#             house_length = len(neighbourhood[i])
#             person_index = random.randint(0, house_length)

#             # find a better way to do this so no infinite loop occurs or find a better way to create the houses
#             if (neighbourhood[i][person_index].get_age() != '0-9'):
#                 self.grocery_stores_list_of_people.append(neighbourhood[i][person_index])
#             else:
#                 i -= 1

#     def grocery_store(self, grocery_store_index):

#         grocery_store_population = [] # list of people at the grocery store

#         for i in range(0, self.number_grocery_stores):
#             # goes through everyone who has the grocery store as their index and adds them to a list
#             if self.which_grocery_store[i] == grocery_store_index:
#                 grocery_store_population.append(self.grocery_stores_list_of_people[i])
#         return grocery_store_population

#     # home
#     def home (self,house_index):
#         resident_list =  self.population.household(house_index) #list of residents in a house
#         resident_list_index = []
#         infected_house = False
#         for i in range (len(resident_list)):
#             resident_list_index.append(resident_list[i].get_index()) #gets the index of each person in the house
#             #if anyone in the house is infected the house is infected
#             if (obj.is_infected() == True for obj in resident_list[i]):
#                 infected_house = True
#         #infect everyone in the house
#         if (infected_house == True):
#             for i in range (len(resident_list)):
#                 if (obj.is_infected() == False for obj in resident_list[i]):
#                     person = self.population.check_individual(resident_list_index[i]).infect(self.nDays)
#                     self.population.update_infected(person.get_index())


#     # interaction function
#     def will_interaction(self, local_population, size_of_location,contact_matrix,busyness):
#         interaction_list = []
#         for i in range(len(local_population)):
#             # get variables of people from local population
#             person = local_population[i]
#             isolation_tend = person.isolation_tendencies
#             placeholder_equation = size_of_location*contact_matrix*busyness*isolation_tend
#             potential_interaction_number = 2  # will be calculated by a bunch of variables that I do not know
#             interaction_number = random.randint(0, potential_interaction_number)
#             interaction_list.append(interaction_number)
#         return interaction_list

#     # determines who will interact with who
#     def who_will_interact(self, interaction_list, local_population):
#         interactions = [] # list of all interaction
#         for i in range (len(local_population)):
#             person_interactions = [] # list of each person's index person i interacts with
#             interaction_number = interaction_list[i]
#             for j in range (interaction_number):
#                 interaction_index = random.randint(0,len(local_population)) #chooses a random person in the list to interact with
#                 if (interaction_list[interaction_index] > 0):
#                     interaction_list[interaction_index] -= 1 #removes an interaction from that persons possible interactions
#                     person_interactions.append(interaction_index) #adds that person to their interaction
#                 else:
#                     #potential infinite loop
#                     j-= 1
#                 interactions.append(person_interactions)
#         return interactions

#     # probability of the virus spreading based on the interactions in the who will interact function
#     def prob_of_spread(self,local_population, who_will_interact):

#         for i in range (len(local_population)):
#             infection_probability = [] # probability of infection for each person
#             interactions = who_will_interact[i] # number of interactions person i had
#             for j in range (len(interactions)):
#                 index = interactions[j] # person j's index
#                 person = local_population[index] #gets person j
#                 if (person.is_infected() == True):
#                     #gathers data from person
#                     prob_of_infection = 0.1 # using info from person
#                     infection_probability.append(prob_of_infection) #adds the probability of infection to a list
#             prob = sum(infection_probability) #sums all the infection probabilities
#             #produces a random number which if within the probability bounds infects the person
#             if random.random()  <= prob:
#                 local_population[i].infect(self.nDays) #infects the person
#                 self.population.update_infected(i)  # update the list of suceptiple and infected people