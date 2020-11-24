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

# probability of someone going out when they're quarantined
Q_GO_PROB = 0

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
            num_diff_sites = abs(round(np.random.normal(loyalty_mean, loyalty_std)))
            
            # Get a list of len num_diff_sites for this person to be associated with now
            person_sites = np.random.choice(num_sites, num_diff_sites, replace=False)
            for site in person_sites:
                # Assign this person to that site
                grade_sites[site].append(person.get_index())
                
        # Convert everything to numpy arrays
        for i, site in enumerate(grade_sites):
            grade_sites[i] = np.array(site)
                
        return grade_sites
                
        
    def will_visit_site(self, site_array, will_go_prob, pop_obj):
        # Function that finds how many people will go to each site of a grade in a given day
        # Returns a list of true or false of size(self.grade_X_sites) that has true for ppl going that day
        
        # to prevent quarantined people from going, their will_go_prob will be Q_GO_PROB (0)
       
        # Could add something here that limits how many sites one person can visit (not real to visit 11 sites a day)
        will_visit_grade = [[] for i in range(len(site_array))]
        for i, site in enumerate(site_array):
            
            prob_attendance = [will_go_prob for j in range(len(site))] 
            
            for j, person in enumerate(site):
                if (pop_obj.get_person(person).is_quarantined == True):
                    prob_attendance[j] = Q_GO_PROB
            
            #if (pop_obj.get_person(i).is_quarantined == True):
            #    site_attendance = np.array([q_go_prob for person in site])
            #else:
            #    site_attendance = np.array([random.random()<will_go_prob for person in site])
            
            site_attendance = np.array([random.random()<=prob_attendance[i] for i in range(len(site))])
            
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
                        