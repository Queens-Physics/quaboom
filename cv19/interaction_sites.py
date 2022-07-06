'''
This file holds the interaction sites class used in simulation.py.
'''
import warnings
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
        sim_obj : :obj:`cv19.simulation.simulation`
            The encompassing simulation obejct hosting the simulation.
        '''

        # Set attributes from config file
        self.load_attributes_from_sim_obj(sim_obj)

        # Generates a list of people that go to different grade X sites
        # len(grade_X_sites) is how many sites there are; len(grade_X_sites[i]) is how many people go to that site
        self.grade_A_sites = self.init_grade(grade_code="A")
        self.grade_B_sites = self.init_grade(grade_code="B")
        self.grade_C_sites = self.init_grade(grade_code="C")
        self.house_sites = deepcopy(self.pop.household)
        self.house_indices = deepcopy(self.pop.house_ppl_i)

        # Students Stuff #
        self.stud_house_sites = deepcopy(self.pop.stud_houses)
        self.stud_house_indices = deepcopy(self.pop.house_stud_i)
        self.lect_sites = self.init_uni(grade_code="LECT")
        self.study_sites = self.init_uni(grade_code="STUDY")
        self.food_sites = self.init_uni(grade_code="FOOD")
        self.res_sites = self.init_res(grade_code="RES")

    def load_attributes_from_sim_obj(self, sim_obj):
        '''Method to load in attributes from the provided simulation class object.

        Sets all objects in the "interaction_sites_data" dictionary key as self
        attributes of the interaction_sites class.

        Parameters
        ----------
        sim_obj : :obj:`cv19.simulation.simulation`
            The encompassing simulation obejct hosting the simulation.
        '''

        attributes = sim_obj.parameters["interaction_sites_data"].keys()
        for attr in attributes:
            setattr(self, attr, sim_obj.parameters["interaction_sites_data"][attr])

        # Get the disease parameters
        d_attributes = sim_obj.disease_parameters["spread_data"].keys()
        for attr in d_attributes:
            setattr(self, attr, sim_obj.disease_parameters["spread_data"][attr])

        # Get the virus type names
        self.variant_codes = sim_obj.variant_codes
        self.variant_code_map = {v_id: v_name for v_name, v_id in self.variant_codes.items()}  # virus ids

        # Set the actual objects now
        self.pop = sim_obj.pop
        self.policy = sim_obj.policy

    def init_grade(self, grade_code):
        '''Method designed to associate members of the population with interaction sites.

        This method initializes all non-student interaction sites by creating a list
        of person indices for each interaction site, for that type of interaction type.

        Parameters
        ----------
        grade_code : str
            Code used to index the values to create this type of site from the config file.

        Returns
        -------
        grade_sites : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding one array for each interaction site of this type. Each nested
            array holds the index of people that are associated with that site (can visit it).
        '''

        loyalty_mean = self.grade_loyalty_means[grade_code]
        loyalty_std = self.grade_loyalty_stds[grade_code]
        students_interact = self.students_participate[grade_code]

        # Calculate number of sites
        num_sites = self.calculate_num_sites(grade_code=grade_code)
        grade_sites = [[] for _ in range(num_sites)]

        for person in self.pop.get_population():
            if students_interact or not (self.students_on and person.job == 'Student'):
                # if students are meant to go to this site
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

    def init_uni(self, grade_code):
        '''Method designed to associate members of the student population with interaction sites.

        This method initializes all student interaction sites by creating a list
        of person indices for each interaction site, for that type of interaction type.

        Parameters
        ----------
        grade_code : str
            Code used to index the values to create this type of site from the config file.

        Returns
        -------
        grade_sites : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding one array for each interaction site of this type. Each nested
            array holds the index of people that are associated with that site (can visit it).
        '''

        loyalty_mean = self.grade_loyalty_means[grade_code]
        loyalty_std = self.grade_loyalty_stds[grade_code]

        # Calculate number of sites
        num_sites = self.calculate_num_sites(grade_code=grade_code)
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

    def init_res(self, grade_code):
        '''Method designed to associate students with the residence interaction site.

        This method initializes the residence interaction sites by creating a list
        of person indices for each interaction site.

        Parameters
        ----------
        grade_code : str
            Code used to index the values to create this type of site from the config file.

        Returns
        -------
        grade_sites : :obj:`np.array` of :obj:`np.array` of :obj:`int`
            An array holding one array for each interaction site of this type. Each nested
            array holds the index of people that are associated with that site (can visit it)
        '''

        loyalty_mean = self.grade_loyalty_means[grade_code]
        loyalty_std = self.grade_loyalty_stds[grade_code]

        # Calculate number of sites
        num_sites = self.calculate_num_sites(grade_code=grade_code)
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

    def calculate_num_sites(self, grade_code):
        '''Method used to calculate the number of sites for an interaction site grade.

        Parameters
        ----------
        grade_code : str
            Code used to index the values to create this type of site from the config file.

        Returns
        -------
        num_sites : int
            The number of sites to be used for that interaction site grade.
        '''

        if self.site_num[grade_code] == 0:
            # Raise a warning
            warnings.warn(f"Site type '{grade_code}' size set to 0. No interaction sites of this type created.")
            return 0
        else:
            return self.site_num[grade_code] if self.site_num[grade_code] is not None else \
                round(self.pop.get_population_size() / self.site_size[grade_code])

    def remove_dead(self):
        '''Method to remove dead agents from interaction site arrays.

        Iterates through each type of site array, and will remove all agents that are
        dead from each array.

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''

        # Create list of all dead agents
        dead_agents = self.pop.get_dead()

        # Site type A
        for i, site_array in enumerate(self.grade_A_sites):
            # Mask where True indicates alive and False indicates dead (note the invert argument)
            mask_alive = np.isin(site_array, dead_agents, invert=True)
            self.grade_A_sites[i] = site_array[mask_alive]

        # Site type B
        for i, site_array in enumerate(self.grade_B_sites):
            mask_alive = np.isin(site_array, dead_agents, invert=True)
            self.grade_B_sites[i] = site_array[mask_alive]

        # Site type C
        for i, site_array in enumerate(self.grade_C_sites):
            mask_alive = np.isin(site_array, dead_agents, invert=True)
            self.grade_C_sites[i] = site_array[mask_alive]

        # Site type lecture
        for i, site_array in enumerate(self.lect_sites):
            mask_alive = np.isin(site_array, dead_agents, invert=True)
            self.lect_sites[i] = site_array[mask_alive]

        # Site type study
        for i, site_array in enumerate(self.study_sites):
            mask_alive = np.isin(site_array, dead_agents, invert=True)
            self.study_sites[i] = site_array[mask_alive]

        # Site type food
        for i, site_array in enumerate(self.food_sites):
            mask_alive = np.isin(site_array, dead_agents, invert=True)
            self.food_sites[i] = site_array[mask_alive]

        # Site type res
        for i, site_array in enumerate(self.res_sites):
            mask_alive = np.isin(site_array, dead_agents, invert=True)
            self.res_sites[i] = site_array[mask_alive]

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

        # Figure out who is going to go to this site type today
        person_ids = np.unique(np.concatenate(site_array))

        # Create array of attendence probabilities
        prob_attendence = [self.quarantine_isolation_factor if self.pop.get_person(person).is_quarantined()
                           else will_go_prob for person in person_ids]

        # Boolean evaluate the array
        person_will_go = np.random.binomial(1, p=prob_attendence).astype(bool)
        person_ids_will_go = person_ids[person_will_go]

        # Assign the people going to a random array they are associated with
        site_index_options = np.arange(len(site_array))
        person_site_choices = [np.random.choice(site_index_options[[person in site for site in site_array]])
                               for person in person_ids_will_go]

        will_visit_grade = [person_ids_will_go[person_site_choices == i] for i in site_index_options]

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
        new_infection_type = np.zeros(self.pop.get_population_size(), dtype=int)

        for ppl_going in will_go_array:

            infected_persons = [index for index in ppl_going if self.pop.get_person(index).is_infected()]
            recovered_persons = [index for index in ppl_going if self.pop.get_person(index).is_recovered()]

            if len(infected_persons) == 0 or (len(infected_persons) + len(recovered_persons) == len(ppl_going)):
                continue  # No ppl to infect here or no one already infected

            # Generate a list of how many interactions ppl have at the site
            num_interactions = self.calc_interactions(site_day_pop=len(ppl_going))

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
                    did_infect = self.interact(p1_obj, p2_obj)
                    if did_infect:
                        if person_1_infected:
                            new_infections[person_2_index] = True
                            new_infection_type[person_2_index] = self.pop.get_person(person_1_index).get_virus_type()
                        else:
                            new_infections[person_1_index] = True
                            new_infection_type[person_1_index] = self.pop.get_person(person_2_index).get_virus_type()

                # Lower the interaction count for those people
                num_interactions[person_1] -= 1
                num_interactions[person_2] -= 1

        #  Update people who get infected only at the end. Assuming if I get CV19 at work, I probably won't spread at the store that night.
        new_infection_indexes = np.where(new_infections)[0]
#         new_infection_type_indexes = np.where(new_infection_type)[0]
        for new_infection in new_infection_indexes:
            self.pop.infect(index=new_infection, virus_type=new_infection_type[new_infection], day=day)

    def calc_interactions(self, site_day_pop):
        '''Method to determine how many interactions a person will have.

        Note
        ----
        Currently the distribution for the number of interactions a given person will have is
        a "triangular" distribution with only one side (a linear distribution). The distribution
        output spans from 0 to site_day_pop/day_hours_scaler, where it is much more likely to have 0
        interactions than the max. day_hours_scaler takes into account that people will not all be
        at the interaction site at the same time, but will be dispersed throughout the 12 hour day.

        As it stands, day_hours_scaler is not a config file parameter, as the hours in the day should not be
        adjusted between simulations. If the need is felt for an adjustable scaling factor, a new (second)
        variable should be introduced.

        Parameters
        ----------
        site_day_pop : `int`
            The total number of people at that specific interaction site this day.

        Returns
        -------
        number_of_interactions : :obj:`np.array` of :obj:`int`
            The number of interactions all people will have within this interaction site.
        '''

        day_hours_scaler = 12

        # Generate a linaer distribution from
        number_of_interactions = np.round(np.random.triangular(left=0, mode=0, right=site_day_pop / day_hours_scaler,
                                                               size=site_day_pop)).astype(int)

        return number_of_interactions

    def interact(self, person_1, person_2):
        '''Method that models the interaction between two people.

        Parameters
        ----------
        person_1 : :obj:`cv19.person.Person`
            First person in the two-way interaction.
        person_2 : :obj:`cv19.person.Person`
            Second person in the two-way interaction.

        Returns
        -------
        : :obj:`bool`
            Whether or not the interaction caused the spread of the infection.
        '''

        p1_infected = person_1.is_infected()
        p2_infected = person_2.is_infected()

        virus_type = person_1.get_virus_type() if p1_infected else person_2.get_virus_type()
        spread_prob = self.base_infection_spread_prob[self.variant_code_map[virus_type]]

        if self.policy.get_mask_mandate():
            p1_mask = person_1.wear_mask()
            p2_mask = person_2.wear_mask()

            P1_INWARD_PROB, P1_OUTWARD_PROB = person_1.mask_type_efficiency()
            P2_INWARD_PROB, P2_OUTWARD_PROB = person_2.mask_type_efficiency()

            if p1_infected:
                if p1_mask:
                    spread_prob *= P1_OUTWARD_PROB
                if p2_mask:
                    spread_prob *= P2_INWARD_PROB

            elif p2_infected:
                if p1_mask:
                    spread_prob *= P1_INWARD_PROB
                if p2_mask:
                    spread_prob *= P2_OUTWARD_PROB

        p1_vaccinated1 = person_1.is_vaccinated()
        p2_vaccinated1 = person_2.is_vaccinated()

        p1_multiplier = person_1.vaccine_type_efficiency() if p1_vaccinated1 else 1
        p2_multiplier = person_2.vaccine_type_efficiency() if p2_vaccinated1 else 1

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
            # Get people in house
            house_size = len(house_indices)
            housemembers = [self.pop.get_population()[ind] for ind in house_indices]
            virus_types = [person.get_virus_type() for person in housemembers]

            # Do interactions between the housemates
            for member1, member2 in combinations(housemembers, 2):
                member1.log_contact(member2, day=day, personal=True)
                member2.log_contact(member1, day=day, personal=True)

            # Check if anyone in the house is infected
            if any(housemembers[i].is_infected() for i in range(house_size)):
                infected_housemembers = [i for i in range(house_size) if housemembers[i].is_infected()]
                virus_types = [virus_types[i] for i in infected_housemembers]
                healthy_housemembers = [i for i in range(house_size) if not housemembers[i].is_infected()]

                for person in healthy_housemembers:
                    virus_id = np.random.choice(a=virus_types)
                    virus_name = self.variant_code_map[virus_id]

                    infection_chance = self.base_infection_spread_prob[virus_name] * self.house_infection_spread_factor
                    caught_infection = random() < infection_chance

                    if caught_infection:
                        if virus_id is None:
                            raise ValueError("House infection has incorrect virus type.")
                        self.pop.infect(index=housemembers[person].get_index(), day=day, virus_type=virus_id)

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
            # Get people in house
            house_size = len(house_indices)
            housemembers = [self.pop.get_population()[ind] for ind in house_indices]
            virus_types = [person.get_virus_type() for person in housemembers]

            # Do interactions between the housemates
            for member1, member2 in combinations(housemembers, 2):
                member1.log_contact(member2, day=day, personal=True)
                member2.log_contact(member1, day=day, personal=True)

            # Check if anyone in the house is infected
            if any(housemembers[i].is_infected() for i in range(house_size)):
                infected_housemembers = [i for i in range(house_size) if housemembers[i].is_infected()]
                virus_types = [virus_types[i] for i in infected_housemembers]
                healthy_housemembers = [i for i in range(house_size) if not housemembers[i].is_infected()]

                for person in healthy_housemembers:
                    virus_id = np.random.choice(a=virus_types)
                    virus_name = self.variant_code_map[virus_id]

                    infection_chance = self.base_infection_spread_prob[virus_name] * self.house_infection_spread_factor
                    caught_infection = random() < infection_chance
                    if caught_infection:
                        if virus_id is None:
                            raise ValueError("House infection has incorrect virus type.")
                        self.pop.infect(index=housemembers[person].get_index(), day=day, virus_type=virus_id)

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
