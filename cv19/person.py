import random
import numpy as np


class Person(object):
    '''A class designed to create individuals to create a population.

    There are currently 26 different attributes set for each person.

    All attributes are passed through the sim_obj, which accesses the simulation
    configuration file.Outlined below are the main object attributes that create a
    person.

    Attributes
    ----------

    '''

    def __init__(self, index, sim_obj, infected=False, recovered=False, dead=False, hospitalized=False, quarantined=False,
                 quarantined_day=None, infected_day=None, recovered_day=None, death_day=None, others_infected=None,
                 cure_days=None, recent_infections=None, age=None, job=None, house_index=0, isolation_tendencies=None,
                 case_severity=None, mask_type=None, has_mask=True):
        '''Method to load in attributes from the provided simulation class object.

        Sets all objects in the "person_data" dictionary key as self attributes of the
        interaction_sites class.

        Parameters
        ----------
        sim_obj :obj:`simulation.simulation`
            The encompassing simulation obejct hosting the simulation
        infected :
        recovered :
        dead :
        hospitalized : int
            Determines if infected the person will go to the hospital, defaults False
        quarantined :
        quarantined_day :
        infected_day :
        recovered_day :
        death_day :
        others_infected :
        recent_infections :
        age : string
            Is an age range the person belongs to
        job :
        house_index :
        isolation_tendencies :
        case_severity :
        mask_type : string
            Determines type of mask worn by person, defaults to None
        has_mask : bool
            Determines if a person will wear a mask or not, defaults to True
        goodness : float
        days_in_lockdown : int
            Records the number of days a person has been under lockdown
        '''

        self.infected = infected
        self.recovered = recovered
        self.dead = dead
        self.hospitalized = hospitalized
        self.quarantined = quarantined
        self.quarantined_day = quarantined_day
        self.infected_day = infected_day
        self.recovered_day = recovered_day
        self.death_day = death_day
        self.others_infected = [] if others_infected is None else others_infected
        self.cure_days = cure_days
        self.recent_infections = recent_infections
        self.index = index
        self.age = age
        self.job = job
        self.household = house_index
        self.isolation_tendencies = isolation_tendencies
        self.case_severity = case_severity
        self.mask_type = mask_type
        self.show_symptoms = False
        self.days_until_symptoms = None
        self.knows_infected = False
        self.will_get_symptoms = False
        self.has_mask = has_mask
        self.test_day = None
        self.has_cold = False
        self.protocol_compliance = None
        self.days_in_lockdown = 0
        # Set the simulaiton object to access the variables
        self.sim_obj = sim_obj

    def is_infected(self):
        '''Method to retrieve if a person is infected. Returns True if infected, False if
        not.

        Returns
        -------
        self.is_infected: :obj:`bool`
        '''
        return self.infected

    def is_recovered(self):
        '''Method to retrieve if a person is recovered. Returns True if recovered, False if
        not.

        Returns
        -------
        self.is_recovered: :obj:`bool`
        '''
        return self.recovered

    def is_dead(self):
        '''Method to retrieve if a person is dead. Returns True if dead, False if not.

        Returns
        -------
        self.is_dead: :obj:`bool`
        '''
        return self.dead

    def is_quarantined(self):
        '''Method to retrieve if a person is quarantined. Returns True if quarantined,
        False if not.

        Returns
        -------
        self.quarantined: :obj:`bool`
        '''
        return self.quarantined

    def is_hospitalzied(self):
        '''Method to retrieve if a person is hospitalized. Returns True if dead, False if
        not.

        Returns
        -------
        self.hospitalized: :obj:`bool`
        '''
        return self.hospitalized

    def set_quarantine(self, day):
        '''Method to set a person to be in quarantine. Sets the day the quarantine begins to the day inputted.
        Parameters
        ----------
        day: int
            The day in the simulation when a person is put into quarantine.
        Returns
        -------
        self.quarantined: :obj:`bool`
        '''

        self.quarantined_day = day
        self.quarantined = True
        return self.quarantined

    def leave_quarantine(self, day):
        ''' Method to determine if a person is done quarantining based on an inputted day.
        Will return True if person is recovered, dead or the inputted day is greater than
        self.sim_obj.quarantine_time.
        Will return False otherwise

        Parameters
        ----------
        day: int
            The current day in the simulation to check agaisnt the day when a person went into quarantine.

        Returns
        -------
        not self.quarantined: :obj:`bool`
        '''
        if self.quarantined_day is None:
            self.quarantined_day = 0
        if self.recovered or self.dead or (day - self.quarantined_day) >= self.sim_obj.quarantine_time:
            self.quarantined = False
            self.show_symptoms = False
            return not self.quarantined
        return not self.quarantined

    def get_quarantine_day(self):
        '''Method to retrieve the day a person is put into quarantine.

        Returns
        -------
        self.quarantined_day: :obj:`int`
        '''
        return self.quarantined_day

    def not_infected_symptoms(self):
        '''Method to randomly infect a person with non COVID19 symptoms.

        Returns
        -------
        self.show_symptoms: :obj:`bool`
        '''
        prob_of_symptom = random.random()
        if prob_of_symptom <= self.sim_obj.cold_prob:
            self.show_symptoms = True
            self.has_cold = True
        return self.show_symptoms

    def set_test_day(self,day):
        '''Method to set the day a person is tested.

        Parameters
        ----------
        day: int
            The day in the simulation when the person was tested.
        '''
        self.test_day = day

    def get_test_day(self):
        '''Method to retrieve the day a person is tested.

        Returns
        -------
        self.test_day: :obj:'int'
        '''
        return self.test_day

    def check_test_day (self, day):
        '''Method to check if the person has been tested in the quarantine time range.
        If the day is greater than the test day is removed.
        If the person had a cold it is also removed.

        Parameters
        ----------
        day: int
            The current day in the simulation to compare against  when the person was tested.
        Returns
        -------
        True if the quarantine time range has passed since they have been last tested, False otherwise
        '''
        if self.test_day is None:
            return False
        elif (day - self.test_day) >= self.quarantine_time:
            self.test_day = None
            self.has_cold = False
            return True
        return False

    def check_symptoms (self, day):
        '''Method to check a persons symtoms based on if they are infected with COVID19 or a cold.

        Parameters
        ----------
        day: int
            The current day in the simulation to compare against  when the person was tested.

        Returns
        -------
        self.show_symptoms: :obj:'bool'
        '''
        if self.will_get_symptoms and (day - self.infected_day) >= self.days_until_symptoms and self.infected or self.has_cold:
            self.show_symptoms = True
        elif not self.infected and not self.has_cold:
            self.show_symptoms = False
        return self.show_symptoms

    # Return index of person
    def get_index(self):
        return self.index

    # Return list of others infected
    def get_others_infected(self):
        return self.others_infected

    # Get list of recent infections (from the last time they infected people)
    def get_recent_infections(self):
        return self.recent_infections

    def get_case_severity(self):
        return self.case_severity

    def get_mask(self):
        '''Method to retrive if a person is wearing a mask.

        Returns
        -------
        self.has_mask: :obj:`bool`
        '''
        return self.has_mask

    # Method to infect a person
    def infect(self, day, cure_days=None):

        d_params = self.sim_obj.disease_parameters

        # Check that they are suseptable (maybe should have that as property?)
        if not self.recovered and not self.infected and not self.dead:
            self.infected = True
            self.infected_day = day
            self.will_get_symptoms = True
            self.days_until_symptoms  = np.random.randint(d_params["days_before_symptoms"]["min"],
                                                          d_params["days_before_symptoms"]["max"])

            # If cure days not specified then choose random number inbetween min and max
            if self.case_severity == 'Mild' or self.case_severity is None:  # If severity not specified, choose Mild
                prob_of_symptom = random.random()
                if prob_of_symptom > d_params["mild_symptom_prob"]:  # probability that the person has mild symtoms
                    # choose number of days after infection when symptoms show
                    self.will_get_symptoms = False
                    self.days_until_symptoms = None

                self.cure_days = np.random.randint(d_params["mild_days"]["min"],
                                                   d_params["mild_days"]["max"]) if cure_days is None else cure_days
            #Assuming that all hospitalization or worse cases will show symptoms
            elif self.case_severity == 'Hospitalization':
                self.cure_days = np.random.randint(d_params["severe_days"]["min"],
                                                   d_params["severe_days"]["max"]) if cure_days is None else cure_days
                self.hospitalized = True
            elif self.case_severity == 'ICU':
                self.cure_days = np.random.randint(d_params["ICU_days"]["min"],
                                                   d_params["ICU_days"]["max"]) if cure_days is None else cure_days
                self.hospitalized = True
            elif self.case_severity == 'Death':
                self.cure_days = np.random.randint(d_params["die_days"]["min"],
                                                   d_params["die_days"]["max"]) if cure_days is None else cure_days
                self.hospitalized = True

            return True

        return False

    # check if someone is quarantined, and if they can come out
    # (if they've quarantined for 14 days)
    def check_quarantine(self, day):
        if self.quarantined:
            days_since_quarantined = day - self.quarantined_day
            if days_since_quarantined >= self.sim_obj.quarantine_time:
                self.quarantined = False
                return False
            return True
        else:  # if not self quarantined
            # if they aren't in quarantine, check if they know they're infected
            #   then put them into quarantine
            if self.case_severity != "Mild":
                # if their symtoms are not mild, quarantine if they're infected
                # assume people in the hospital aren't spreading it either
                self.quarantined_day = day
                self.quarantined = True

                return True
            return False

    # Method that checks if a person is past their cure time and will cure them
    # Returns True if they were cured, False if not
    def check_cured(self, day):

        if self.infected and not self.recovered:

            days_since_infected = day - self.infected_day
            # Checks cure timeline
            if days_since_infected >= self.cure_days:
                # Resets values to cure them
                self.infected = False
                self.recovered = True
                self.recovered_day = day
                self.will_get_symptoms = False
                self.knows_infected = False
                self.days_until_symptoms = None
                self.show_symptoms = False
                self.hospitalized = False

                return True
        return False

    def check_dead(self, day): # checking that case_severity==death outside of the loop

        if self.infected:

            days_since_infected = day - self.infected_day
            # Checks death timeline
            if days_since_infected >= self.cure_days:
                self.infected = False
                self.dead = True
                self.death_day = day

                return True
        return False

    def check_hospitalized(self):
        '''Method to check if a person will be hospitalized or not once being infected.

        Returns
        -------
        True if hospitalized and False if not
        '''
        if self.infected:
            if self.case_severity == 'Hospitalization' or self.case_severity == 'ICU' or self.case_severity == 'Death':
                self.hospitalized = True

            return True
        return False

    def wear_mask(self):
        '''Method to check if a person will wear a mask.

        Returns
        -------
        True if wearing a mask and False if not.
        '''
        mask_options = np.random.uniform()

        if self.has_mask:
            if mask_options/self.protocol_compliance > self.sim_obj.wear_mask_properly:
                return False  #False = not wearing a mask
            else:
                return True  #True = wearing a mask
        else:
            return False

    def mask_type_efficiency(self):
        '''Method to determines what the inward and outward efficiency of the spread will
        be based on the type of mask worn.

        Returns
        -------
        self.sim_obj.surgical_inward_eff, self.sim_obj.surgical_outward_eff : :obj:`float`.
        '''
        if self.has_mask and self.mask_type == "Surgical":
            return self.sim_obj.surgical_inward_eff, self.sim_obj.surgical_outward_eff
        elif self.has_mask and self.mask_type == "Non-surgical":
            return self.sim_obj.nonsurgical_inward_eff, self.sim_obj.nonsurgical_outward_eff
        else:
            return 1, 1  #Not wearing a mask so this will function will not effect their change of getting the virus

    def set_protocol_compliance(self, house_size):
        '''Method to set the initial protocol compliance value of a person.

        Parameters
        ----------
        house_size: int
            Number of people living in said persons house.

        Returns
        -------
        self.protocol_compliance: :obj:'float'
        '''

        if self.protocol_compliance is None: #If no protocol compliance score is defined
            self.protocol_compliance = self.sim_obj.goodness

        if house_size > len(self.sim_obj.protocol_compliance_house_prob): #Sets the house size to the largest house size probability if the house size is larger than that number
            house_size = len(self.sim_obj.protocol_compliance_house_prob)
        if random.random() < self.sim_obj.protocol_compliance_house_prob[house_size - 1]:
            self.protocol_compliance *= self.sim_obj.protocol_compliance_house_reduction[house_size - 1] # changes the persons protocol compliance based on house size

        if random.random() < self.sim_obj.protocol_compliance_age_prob[self.age]:
            self.protocol_compliance *= self.sim_obj.protocol_compliance_age_reduction[self.age]

        if random.random() < self.sim_obj.protocol_compliance_case_severity_prob[self.case_severity]:
            self.protocol_compliance *= self.sim_obj.protocol_compliance_case_severity_reduction[self.case_severity] #changes protocol compliance based on how severity of a potential case
        return self.protocol_compliance

    def update_protocol_compliance(self, lockdown_level, old_lockdown_mandate):
        '''Method to update the protocol compliance value of a person.

        Parameters
        -------
        lockdown_level: bool
            Paramter to check if the lockdown is on (True)
        old_lockdown_mandate: bool
            Paramter to check what the lockdown was the day before the current one
        Returns
        -------
        self.protocol_compliance: :obj:'float'
        '''
        if self.protocol_compliance is None: #If no protocol compliance it is defined
            self.protocol_compliance =  self.sim_obj.protocol_compliance

        if self.days_in_lockdown > self.sim_obj.protocol_compliance_lockdown_length_threshold and random.random() < self.sim_obj.protocol_compliance_lockdown_prob: #as the lockdown length increases decrease the protocol compliance
            self.protocol_compliance *= self.sim_obj.protocol_compliance_lockdown_length_reduction

        if lockdown_level != old_lockdown_mandate:
            # when the lockdown starts increase the protocol compliance of a person
            if lockdown_level and random.random() < self.sim_obj.protocol_compliance_lockdown_prob:
                self.protocol_compliance *= self.sim_obj.protocol_compliance_lockdown_reduction
            # when the lockdown ends decerase the protocol compliance of a person
            elif lockdown_level is False and random.random() < self.sim_obj.protocol_compliance_lockdown_prob:
                self.protocol_compliance /= self.sim_obj.protocol_compliance_lockdown_reduction
        return self.protocol_compliance

    def get_protocol_compliance(self):
        '''Method to retrieve the protocol compliance value of a person.

        Returns
        -------
        self.protocol_compliance: :obj:'float'
        '''
        return self.protocol_compliance

    def update_lockdown_days(self, lockdown_level):
        '''Method to change the number of days a person is in a lockdown or quarantine.

        Returns
        -------
        self.days_in_lockdown: :obj:'int'
        '''
        if lockdown_level or self.quarantined:
            self.days_in_lockdown += 1
        elif self.days_in_lockdown != 0:
            self.days_in_lockdown -= 1
        return self.days_in_lockdown
