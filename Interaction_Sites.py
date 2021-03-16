import random
import numpy as np

# __init__ parameters
GRADE_A_PER_POP = 1./500
GRADE_B_PER_POP = 1./500
GRADE_C_PER_POP = 1./500

A_LOYALTY_MEAN, A_LOYALTY_STD = 4, 2
B_LOYALTY_MEAN, B_LOYALTY_STD = 1, 1
C_LOYALTY_MEAN, C_LOYALTY_STD = 1, .5

# House spread parameters
HOUSE_SPREAD_PROB = 0.2

BASE_INFECTION_SPREAD_PROB = 0.15
HOUSE_INFECTION_SPREAD_PROB = BASE_INFECTION_SPREAD_PROB*(1.25)

# probability of someone going out when they're quarantined
Q_GO_PROB = 0

class Interaction_Sites:

    ###### NEW CLASS ######
    def __init__(self, pop_obj):

        self.pop = pop_obj
        self.policy = pop_obj.policy
        # Grade A means ones you go to different ones of (resturants, gas station, retail stores)
        # Grade B means usually the same one, but sometimes not (gym, grocery store)
        # Grade C means almost always go to the same one (office, school)

        # Generates a list of ppl that go to different grade X sites
        # len(grade_X_sites) is how many sites there are; len(grade_X_sites[i]) is how many ppl go to that site

        self.grade_A_sites = np.array(self.init_grade(GRADE_A_PER_POP, A_LOYALTY_MEAN, A_LOYALTY_STD))
        self.grade_B_sites = np.array(self.init_grade(GRADE_B_PER_POP, B_LOYALTY_MEAN, B_LOYALTY_STD))
        self.grade_C_sites = np.array(self.init_grade(GRADE_C_PER_POP, C_LOYALTY_MEAN, C_LOYALTY_STD))
        self.house_sites = np.array(pop_obj.household).copy()


    def init_grade(self, grade_pop_size, loyalty_mean, loyalty_std):
        # Find out how many sites there should be - guessing right now
        num_sites = round(self.pop.get_population_size()*grade_pop_size)
        grade_sites = [[] for _ in range(num_sites)]

        for person in self.pop.get_population():
            # Assign people to this specific site
            num_diff_sites = abs(round(np.random.normal(loyalty_mean, loyalty_std)))
            num_diff_sites = num_diff_sites if num_diff_sites <= num_sites else num_sites
            # Get a list of len num_diff_sites for this person to be associated with now
            person_sites = np.random.choice(num_sites, num_diff_sites, replace=False)
            for site in person_sites:
                # Assign this person to that site
                grade_sites[site].append(person.get_index())

        # Convert everything to numpy arrays
        grade_sites = [np.asarray(site) for site in grade_sites]

        return grade_sites


    def will_visit_site(self, site_array, will_go_prob):
        # Function that finds how many people will go to each site of a grade in a given day
        # Returns a list of true or false of size(self.grade_X_sites) that has true for ppl going that day

        # to prevent quarantined people from going, their will_go_prob will be Q_GO_PROB (0)

        # Could add something here that limits how many sites one person can visit (not real to visit 11 sites a day)
        will_visit_grade = [[] for _ in range(len(site_array))]
        for i, site in enumerate(site_array):
            # initialize probability array, all of the same probability
            prob_attendance = np.zeros(shape=len(site)) + will_go_prob

            # change the probabilities for quarantined people
            for j, person in enumerate(site):
                if self.pop.get_person(person).is_quarantined():
                    prob_attendance[j] = Q_GO_PROB

            site_attendance = np.random.uniform(size=prob_attendance.shape[0]) < prob_attendance
            will_visit_grade[i] = site[site_attendance]

        return will_visit_grade


    def site_interaction(self, will_go_array, day):
        # Find out how many interactions each person has at the site - FUNCTION IS PRETTY SLOW RN
        # Should deal with case where one person is left with more than one interaction
        new_infections = np.zeros(self.pop.get_population_size(), dtype=bool)

        for ppl_going in will_go_array:

            infected_persons = [index for index in ppl_going if self.pop.get_person(index).is_infected()]
            recovered_persons = [index for index in ppl_going if self.pop.get_person(index).is_recovered()]

            if len(infected_persons) == 0 or (len(infected_persons) + len(recovered_persons) == len(ppl_going)):
                continue # No ppl to infect here or no one already infected

            # Generate a list of how many interactions ppl have at the site
            num_interactions = np.array([self.calc_interactions(person_index, len(ppl_going))
                                         for person_index in ppl_going])

            while np.sum(num_interactions > 0) > 1:
                # grab the highest interactor
                person_1 = np.argmax(num_interactions)
                # find a random interactor for them to pair with (that is not them)
                person_2 = np.random.randint(num_interactions.shape[0])
                while person_2 == person_1 or num_interactions[person_2] <= 0:
                    person_2 = np.random.randint(num_interactions.shape[0])

                # Get the actual people at these indexes
                person_1_index = ppl_going[person_1]
                person_2_index = ppl_going[person_2]

                # Check to make sure one is infected
                person_1_infected = self.pop.get_person(person_1_index).is_infected()
                person_2_infected = self.pop.get_person(person_2_index).is_infected()

                if person_1_infected != person_2_infected:
                    # Have an interaction between those people
                    did_infect = self.interact(person_1_index, person_2_index)
                    if did_infect:
                        if person_1_infected:
                            new_infections[person_2_index] = True
                        else:
                            new_infections[person_1_index] = True

                # Lower the interaction count for those people
                num_interactions[person_1] -= 1
                num_interactions[person_2] -= 1


        # Update people who get infected only at the end (if i get CV19 at work, prolly wont spread at the store that night ?)
        new_infection_indexes = np.where(new_infections)[0]
        for new_infection in new_infection_indexes:
            self.pop.infect(index=new_infection, day=day)


    def calc_interactions(self, person_index, how_busy):
        # This will be some function that returns how many interactions for this person
        upper_interaction_bound = 10
        lower_interaction_bound = 0  # Random numbers at the moment

        return np.random.randint(lower_interaction_bound, upper_interaction_bound)
         
    def interact(self, person_1, person_2):
        # Function that models the interaction between two people, and will return if interaction spread
        if self.policy.get_mask_mandate==False:
            spread_prob = BASE_INFECTION_SPREAD_PROB
        else:
            p1Mask = self.pop.get_person(person_1).wear_mask()
            p2Mask = self.pop.get_person(person_2).wear_mask()
            p1Infected = self.pop.get_person(person_1).is_infected()
            p2Infected = self.pop.get_person(person_2).is_infected()
            P1_INWARD_PROB, P1_OUTWARD_PROB = self.pop.get_person(person_1).mask_type_efficiency()
            P2_INWARD_PROB, P2_OUTWARD_PROB = self.pop.get_person(person_2).mask_type_efficiency()

            if p1Infected:
                if p1Mask and p2Mask: spread_prob = BASE_INFECTION_SPREAD_PROB*P1_OUTWARD_PROB*P2_INWARD_PROB
                elif p1Mask: spread_prob = BASE_INFECTION_SPREAD_PROB*P1_OUTWARD_PROB
                elif p2Mask: spread_prob = BASE_INFECTION_SPREAD_PROB*P2_INWARD_PROB
                else: spread_prob = BASE_INFECTION_SPREAD_PROB

            else:
                if p1Mask and p2Mask: spread_prob = BASE_INFECTION_SPREAD_PROB*P2_OUTWARD_PROB*P1_INWARD_PROB
                elif p1Mask: spread_prob = BASE_INFECTION_SPREAD_PROB*P1_INWARD_PROB
                elif p2Mask: spread_prob = BASE_INFECTION_SPREAD_PROB*P2_OUTWARD_PROB
                else: spread_prob = BASE_INFECTION_SPREAD_PROB
        
        return random.random() < spread_prob
   
    def house_interact(self, day):
        # It is assumed that if people go to the same home they will interact with eachother
        house_count = 0
        for i in range(len(self.house_sites)):
            # Get ppl in house
            house_size = self.house_sites[i]
            housemembers = self.pop.get_population()[house_count:house_count+house_size]
            house_count += house_size

            # Check if anyone in the house is infected
            infected_housemembers = [i for i in range(house_size) if housemembers[i].is_infected() == True]

            if len(infected_housemembers)>0:
                healthy_housemembers = [i for i in range(house_size) if housemembers[i].is_infected() == False]

                for person in healthy_housemembers:
                    # This should be more complicated and depend on len(infectpplinhouse)
                    infection_chance = HOUSE_INFECTION_SPREAD_PROB
                    caught_infection = random.random()<infection_chance
                    if caught_infection:
                        self.pop.infect(index=housemembers[person].get_index(), day=day)

    # Function thats tests the symtomatic individuals as well as brining them in and out of quarentine
    def testing_site (self, tests_per_day, day): 
        #tests per day is number of postive tests per day as we ignore negative tests
        self.pop.update_symptomatic(day)
        self.pop.get_tested(tests_per_day, day)

    def get_grade_A_sites(self):
        return self.grade_A_sites.copy()

    def get_grade_B_sites(self):
        return self.grade_B_sites.copy()

    def get_grade_C_sites(self):
        return self.grade_C_sites.copy()

