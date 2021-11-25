'''
This file holds the interaction sites class used in simulation.py.
'''
from random import random
from copy import deepcopy
from itertools import combinations

import numpy as np

class Interaction_Sites:
    '''A class designed to host interactions between persons within specific locations.

    There are currently 7 different locations that can host interactions between
    person objects.

    All attributes are passed through the sim_obj, which accesses the simulation
    configuration file. Outlined below are the main object attributes that provide the
    interaction functionality.

    Attributes
    ----------
    grade_A_sites : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        Designed to represent resturants, gas stations, retail stores, etc. Any location where you
        do not visit often, but attend a wide variety of them.
    grade_B_sites : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        Designed to represent a gym, grocery store, etc. Any location where
        you visit semi-often, and are likly to visit the same one, but this may varry.
    grade_C_sites : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        Designed to represent offices or schools. Any location where they are
        visited almost every workday, and you almost always visit the same one.
    house_sites : :obj:`np.array` of :obj:`list` of :obj:`int`
        Visited by every person each day, and hosts interactions between members
        of the same household. Infection spread at home is not defined by explicit contacts,
        but by a known spread factor.
    lect_sites : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        Designed to replicate university lecture hall interactions. They are only visited by students.
    study_sites : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        Designed to replicate study environments at university, on-campus (library, bookable rooms, ...).
        They are only visited by students.
    food_sites : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        Designed to replicate cafeteria and restaurant interactions on-campus. Only visited by students.
    res_sites : :obj:`list` of :obj:`np.array` of :obj:`int`
        Designed to replicate the student residences on campus. They are only visited by first year students.
    stud_house_sites : :obj:`np.array` of :obj:`list` of :obj:`int`
        Visited by every student each day, and hosts interactions between members
        of the same household. Infection spread at home is not defined by explicit contacts,
        but by a known spread factor.
    '''

    def __init__(self, sim_obj):
        ''' __init__ method docstring.

        Parameters
        ----------
        sim_obj : :obj:`simulation class`
            The encompassing simulation obejct hosting the simulation.

        '''

        # Set attributes from config file
        self.load_attributes_from_sim_obj(sim_obj)

        # Generates a list of ppl that go to different grade X sites
        # len(grade_X_sites) is how many sites there are; len(grade_X_sites[i]) is how many ppl go to that site
        self.grade_A_sites = self.init_grade(self.grade_per_pop["A"],
                                             self.grade_loyalty_means["A"],
                                             self.grade_loyalty_stds["A"],
                                             self.students_participate["A"])
        self.grade_B_sites = self.init_grade(self.grade_per_pop["B"],
                                             self.grade_loyalty_means["B"],
                                             self.grade_loyalty_stds["B"],
                                             self.students_participate["B"])
        self.grade_C_sites = self.init_grade(self.grade_per_pop["C"],
                                             self.grade_loyalty_means["C"],
                                             self.grade_loyalty_stds["C"],
                                             self.students_participate["C"])
        self.house_sites = deepcopy(self.pop.household)
        self.house_indices = deepcopy(self.pop.house_ppl_i)

        # Students Stuff #
        self.stud_house_sites = deepcopy(self.pop.stud_houses)
        self.stud_house_indices = deepcopy(self.pop.house_stud_i)
        self.lect_sites = self.init_uni(self.grade_per_pop["LECT"],
                                        self.grade_loyalty_means["LECT"],
                                        self.grade_loyalty_stds["LECT"])
        self.study_sites = self.init_uni(self.grade_per_pop["STUDY"],
                                         self.grade_loyalty_means["STUDY"],
                                         self.grade_loyalty_stds["STUDY"])
        self.food_sites = self.init_uni(self.grade_per_pop["FOOD"],
                                        self.grade_loyalty_means["FOOD"],
                                        self.grade_loyalty_stds["FOOD"])
        self.res_sites = self.init_res(self.grade_per_pop["RES"],
                                       self.grade_loyalty_means["RES"],
                                       self.grade_loyalty_stds["RES"])

    def load_attributes_from_sim_obj(self, sim_obj):
        '''Method to load in attributes from the provided simulation class object.

        Sets all objects in the "interaction_sites_data" dictionary key as self
        attributes of the interaction_sites class.

        Parameters
        ----------
        sim_obj : :obj:`simulation class`
            The encompassing simulation obejct hosting the simulation.

        '''

        attributes = sim_obj.parameters["interaction_sites_data"].keys()
        for attr in attributes:
            setattr(self, attr, sim_obj.parameters["interaction_sites_data"][attr])

        # Get the disease parameters
        d_attributes = sim_obj.disease_parameters["spread_data"].keys()
        for attr in d_attributes:
            setattr(self, attr, sim_obj.disease_parameters["spread_data"][attr])

        self.house_infection_spread_prob = self.base_infection_spread_prob * self.house_infection_spread_factor

        # Set the actual objects now
        self.pop = sim_obj.pop
        self.policy = sim_obj.policy

    def init_grade(self, grade_pop_size, loyalty_mean, loyalty_std, students_interact):
        '''Method designed to associate members of the population with interaction sites

        This method initializes all non-student interaction sites by creating a list
        of person indices for each interaction site, for that type of interaction type.

        Parameters
        ----------
        grade_pop_size : int
            Number of people per interaction site. Determines how many interaction sites
            there will be across the population.
        loyalty_mean : float
            The mean number of this type of sites that each person will be associated with.
        loyalty_std : float
            The standard deviation in the number of sites of this type a person will be
            associated with.
        students_interact : boolean
            Whether or not students will attend the interaction site being initialized

        Returns
        -------
        grade_sites : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding one array for each interaction site of this type. Each nested
            array holds the index of people that are associated with that site (can visit it).

        '''
        # Find out how many sites there should be - guessing right now
        num_sites = round(self.pop.get_population_size()/grade_pop_size)
        grade_sites = [[] for _ in range(num_sites)]

        for person in self.pop.get_population():
            if students_interact or not (self.students_on and person.job == 'Student'):
                #if students are meant to go to this site
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

    def init_uni(self, grade_pop_size, loyalty_mean, loyalty_std):
        '''Method designed to associate members of the student population with interaction sites

        This method initializes all student interaction sites by creating a list
        of person indices for each interaction site, for that type of interaction type.

        Parameters
        ----------
        grade_pop_size : int
            Number of people per interaction site. Determines how many interaction sites
            there will be across the population.
        loyalty_mean : float
            The mean number of this type of sites that each person will be associated with.
        loyalty_std : float
            The standard deviation in the number of sites of this type a person will be
            associated with.

        Returns
        -------
        grade_sites : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding one array for each interaction site of this type. Each nested
            array holds the index of people that are associated with that site (can visit it)

        '''
        num_sites = round(self.pop.get_student_pop_size()/grade_pop_size)
        grade_sites = [[] for _ in range(num_sites)]

        for student in self.pop.get_population():
            if student.job == 'Student':
                # Assign people to this specific site
                num_diff_sites = abs(round(np.random.normal(loyalty_mean, loyalty_std)))
                num_diff_sites = num_diff_sites if num_diff_sites <= num_sites else num_sites
                # Get a list of len num_diff_sites for this person to be associated with now
                student_sites = np.random.choice(num_sites, num_diff_sites, replace=False)
                for site in student_sites:
                    # Assign this person to that site
                    grade_sites[site].append(student.get_index())

        # Convert everything to numpy arrays
        grade_sites = [np.asarray(site) for site in grade_sites]

        return grade_sites

    def init_res(self, grade_pop_size, loyalty_mean, loyalty_std):
        '''Method designed to associate students with the residence interaction site

        This method initializes the residence interaction sites by creating a list
        of person indices for each interaction site.

        Parameters
        ----------
        grade_pop_size : int
            Number of people per residence section. Determines how many interaction sites
            there will be across the population.
        loyalty_mean : float
            The mean number of this type of sites that each person will be associated with.
        loyalty_std : float
            The standard deviation in the number of sites of this type a person will be
            associated with.

        Returns
        -------
        grade_sites : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding one array for each interaction site of this type. Each nested
            array holds the index of people that are associated with that site (can visit it)

        '''

        num_sites = round(self.pop.get_res_size()/grade_pop_size)
        grade_sites = [[] for _ in range(num_sites)]

        for room in self.pop.get_residences():
            for student_i in self.stud_house_indices[room]:
                # Assign people to this specific site
                num_diff_sites = abs(round(np.random.normal(loyalty_mean, loyalty_std)))
                num_diff_sites = num_diff_sites if num_diff_sites <= num_sites else num_sites
                # Get a list of len num_diff_sites for this person to be associated with now
                student_sites = np.random.choice(num_sites, num_diff_sites, replace=False)
                for site in student_sites:
                    # Assign this person to that site
                    grade_sites[site].append(student_i)

        # Convert everything to numpy arrays
        grade_sites = [np.asarray(site) for site in grade_sites]

        return grade_sites

    def will_visit_site(self, site_array, will_go_prob):
        '''Method to determine who will visit a site on a given day.

        Generates a boolean list for each individual interaction site in site_array,
        indicating what people from the list will visit that site on a given day. Accounts
        for quarantined people by setting their will_go_prob value to
        self.quarantine_isolation_factor.

        Parameters
        ----------
        site_array : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding lists (one for each interaction site) of the index of each person
            associated with each of the individual sites.
        will_go_prob : float
            The probability that any given person in site_array will visit this type of site.

        Returns
        -------
        will_visit_grade : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding an array for each site of this interaction site type.
            Each individual list holds the indexes of people that will visit that site for this day.
        '''

        # Could add something here that limits how many sites one person can visit (not real to visit 11 sites a day)
        will_visit_grade = [[] for _ in range(len(site_array))]
        for i, site in enumerate(site_array):
            # initialize probability array, all of the same probability
            prob_attendance = np.zeros(shape=len(site)) + will_go_prob

            # change the probabilities for quarantined people
            for j, person in enumerate(site):
                if self.pop.get_person(person).is_quarantined():
                    prob_attendance[j] = self.quarantine_isolation_factor

            site_attendance = np.random.uniform(size=prob_attendance.shape[0]) < prob_attendance
            will_visit_grade[i] = site[site_attendance]

        return will_visit_grade

    def site_interaction(self, will_go_array, day, personal):
        '''Method that hosts interactions between people for an interaction site type.

        This method manages interactions between people going to the same interaction
        site this day. Currently, all people that visit the same site on a day have a
        chance to interact with each other. Does not provide a return value, all
        infections are managed within the function.

        Parameters
        ----------
        will_go_array : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding an array for each site of this interaction site type. Each individual list
            holds the indexes of people that will visit that site for this day.
        day : int
            The day value that this function is being called on in the encompassing simulation class.
            Used as input to the infect function after infections have been determined.

        '''
        new_infections = np.zeros(self.pop.get_population_size(), dtype=bool)

        for ppl_going in will_go_array:

            infected_persons = [index for index in ppl_going if self.pop.get_person(index).is_infected()]
            recovered_persons = [index for index in ppl_going if self.pop.get_person(index).is_recovered()]

            if len(infected_persons) == 0 or (len(infected_persons) + len(recovered_persons) == len(ppl_going)):
                continue # No ppl to infect here or no one already infected

            # Generate a list of how many interactions ppl have at the site
            num_interactions = np.array([self.calc_interactions() for person_index in ppl_going])

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

                # Getting the Person objects and logging the contacts
                p1_obj = self.pop.get_person(person_1_index)
                p2_obj = self.pop.get_person(person_2_index)
                p1_obj.log_contact(p2_obj, day=day, personal=personal)
                p2_obj.log_contact(p1_obj, day=day, personal=personal)

                # Check to make sure one is infected
                person_1_infected = p1_obj.is_infected()
                person_2_infected = p2_obj.is_infected()

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

        #  Update people who get infected only at the end (if i get CV19 at work, prolly wont spread at the store that night ?)
        new_infection_indexes = np.where(new_infections)[0]
        for new_infection in new_infection_indexes:
            self.pop.infect(index=new_infection, day=day)

    def calc_interactions(self):
        '''Method to determine how many interactions a person will have.

        Note
        ----
        This function should really be improved, and calibrated with real data. Current
        values were arbitrarily chosen.

        Returns
        -------
        number_of_interactions : int
            The number of interactions this person will have within their interaction site.

        '''

        # This will be some function that returns how many interactions for this person
        upper_interaction_bound = 5
        lower_interaction_bound = 0  # Random numbers at the moment
        number_of_interactions = np.random.randint(lower_interaction_bound, upper_interaction_bound)

        return number_of_interactions

    def interact(self, person_1, person_2):
        '''Method that models the interaction between two people.

        Parameters
        ----------
        person_1 : :obj:`person.Person`
            First person in the two-way interaction.
        person_2 : :obj:`person.Person`
            Second person in the two-way interaction.

        Returns
        -------
        : :obj:`bool`
            Whether or not the interaction caused the spread of the infection.

        '''
        if not self.policy.get_mask_mandate:
            spread_prob = self.base_infection_spread_prob
        else:
            p1Mask = self.pop.get_person(person_1).wear_mask()
            p2Mask = self.pop.get_person(person_2).wear_mask()
            p1Infected = self.pop.get_person(person_1).is_infected()
            P1_INWARD_PROB, P1_OUTWARD_PROB = self.pop.get_person(person_1).mask_type_efficiency()
            P2_INWARD_PROB, P2_OUTWARD_PROB = self.pop.get_person(person_2).mask_type_efficiency()

            if p1Infected:
                if p1Mask and p2Mask:
                    spread_prob = self.base_infection_spread_prob*P1_OUTWARD_PROB*P2_INWARD_PROB
                elif p1Mask:
                    spread_prob = self.base_infection_spread_prob*P1_OUTWARD_PROB
                elif p2Mask:
                    spread_prob = self.base_infection_spread_prob*P2_INWARD_PROB
                spread_prob = self.base_infection_spread_prob

            else:
                if p1Mask and p2Mask:
                    spread_prob = self.base_infection_spread_prob*P2_OUTWARD_PROB*P1_INWARD_PROB
                elif p1Mask:
                    spread_prob = self.base_infection_spread_prob*P1_INWARD_PROB
                elif p2Mask:
                    spread_prob = self.base_infection_spread_prob*P2_OUTWARD_PROB
                else:
                    spread_prob = self.base_infection_spread_prob

        p1Vaccinated1 = self.pop.get_person(person_1).is_vaccinated()
        p2Vaccinated1 = self.pop.get_person(person_2).is_vaccinated()

        p1_multiplier = self.pop.get_person(person_1).vaccine_type_efficiency() if p1Vaccinated1 else 1
        p2_multiplier = self.pop.get_person(person_2).vaccine_type_efficiency() if p2Vaccinated1 else 1

        spread_prob *= (p1_multiplier * p2_multiplier)

        return random() < spread_prob

    def house_interact(self, day):
        '''Method to manage interactions between members of the same household.

        Determines if any infection will spread among members of the same household. Different
        from interaction sites in the fact that contacts are not calculated, but assumed to happen
        between all house members. Does not have a return value, infections are managed internally.

        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.
            Used as input to the infect function after infections have been determined.

        '''

        for house_indices in self.house_indices:
            # Get ppl in house
            house_size = len(house_indices)
            housemembers = [self.pop.get_population()[ind] for ind in house_indices]

            # Do interactions between the housemates
            for member1, member2 in combinations(housemembers, 2):
                member1.log_contact(member2, day=day, personal=True)
                member2.log_contact(member1, day=day, personal=True)

            # Check if anyone in the house is infected
            if any(housemembers[i].is_infected() for i in range(house_size)):
                healthy_housemembers = [i for i in range(house_size) if not housemembers[i].is_infected()]

                for person in healthy_housemembers:
                    # This should be more complicated and depend on len(infectpplinhouse)
                    infection_chance = self.house_infection_spread_prob
                    caught_infection = random() < infection_chance
                    if caught_infection:
                        self.pop.infect(index=housemembers[person].get_index(), day=day)

    def student_house_interact(self, day):
        '''Method to manage interactions between members of the same student household.

        Determines if any infection will spread among members of the same household. Different
        from interaction sites in the fact that contacts are not calculated, but assumed to happen
        between all house members. Does not have a return value, infections are managed internally.

        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.
            Used as input to the infect function after infections have been determined.

        '''

        for house_indices in self.stud_house_indices:
            # Get ppl in house
            house_size = len(house_indices)
            housemembers = [self.pop.get_population()[ind] for ind in house_indices]

            # Check if anyone in the house is infected
            if any(housemembers[i].is_infected() for i in range(house_size)):
                healthy_housemembers = [i for i in range(house_size) if housemembers[i].is_infected()]

                for person in healthy_housemembers:
                    # This should be more complicated and depend on len(infectpplinhouse)
                    infection_chance = self.house_infection_spread_prob
                    caught_infection = random() < infection_chance
                    if caught_infection:
                        self.pop.infect(index=housemembers[person].get_index(), day=day)

    def testing_site(self, tests_per_day, day):
        '''Method to update status of symptoms and run the testing sites code.

        Parameters
        ----------
        tests_per_day : int
            The max number of available tests for this given day.
        day : int
            The day value that this function is being called on in the encompassing simulation class.

        '''

        self.pop.random_symptomatic()
        self.pop.update_symptomatic(day)
        self.pop.get_tested(tests_per_day, day)

    def get_grade_A_sites(self):
        '''Method to return a copy of the grade_A_sites attribute.

        Returns
        -------
        self.grade_A_sites.copy() : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        '''
        return deepcopy(self.grade_A_sites)

    def get_grade_B_sites(self):
        '''Method to return a copy of the grade_B_sites attribute.

        Returns
        -------
        self.grade_B_sites.copy() : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        '''
        return deepcopy(self.grade_B_sites)

    def get_grade_C_sites(self):
        '''Method to return a copy of the grade_C_sites attribute.

        Returns
        -------
        self.grade_C_sites.copy() : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        '''
        return deepcopy(self.grade_C_sites)

    def get_lect_sites(self):
        '''Method to return a copy of the lect_sites attribute.

        Returns
        -------
        self.lect_sites.copy() : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        '''
        return deepcopy(self.lect_sites)

    def get_study_sites(self):
        '''Method to return a copy of the study_sites attribute.

        Returns
        -------
        self.study_sites.copy() : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        '''
        return deepcopy(self.study_sites)

    def get_food_sites(self):
        '''Method to return a copy of the food_sites attribute.

        Returns
        -------
        self.food_sites.copy() : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        '''
        return deepcopy(self.food_sites)

    def get_res_sites(self):
        '''Method to return a copy of the res_sites attribute.

        Returns
        -------
        self.res_sites.copy() : :obj:`np.array` of :obj:`list` of :obj:`np.array` of :obj:`int`
        '''
        return deepcopy(self.res_sites)
