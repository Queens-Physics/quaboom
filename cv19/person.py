from random import random

import numpy as np


class Person(object):
    """A class designed to create individuals to create a population.

    There are currently 26 different attributes set for each person.

    All attributes are passed through the sim_obj, which accesses the simulation
    configuration file.Outlined below are the main object attributes that create a
    person.

    Attributes
    ----------

    """

    def __init__(self, index, sim_obj, infected=False, recovered=False, dead=False, hospitalized=False, ICU=False,
                 quarantined=False, quarantined_day=None, infected_day=None, recovered_day=None, death_day=None,
                 others_infected=None, cure_days=None, recent_infections=None, vaccinated=False, vaccine_type=None,
                 age=None, job=None, house_index=0, isolation_tendencies=None, case_severity=None, mask_type=None,
                 has_mask=True, virus_type=None, days_until_symptoms=None):
        """Method to load in attributes from the provided simulation class object.

        Sets all objects in the "person_data" dictionary key as self attributes of the
        InteractionSites class.

        Parameters
        ----------
        sim_obj :obj:`simulation.simulation`
            The encompassing simulation object hosting the simulation.
        infected : bool
            Determines if person is infected or not, defaults False.
        recovered : bool
            Determines if person is recovered or not, defaults False.
        dead : bool
            Determines if infected person will die, defaults False.
        ICU : bool
            Determines if infected person will go to the ICU, defaults False.
        hospitalized : bool
            Determines if infected person will go to the hospital, defaults False.
        quarantined : bool
            Determines if person is quarentined or not, defaults False.
        quarantined_day : int
            The day a person is put into quarantine, defaults None.
        vaccinated : bool
            Determines if a person is vaccinated or not, defaults to True.
        vaccine_type : string
            Determines type of vaccine received by person, defaults to None.
        infected_day : int
            The day a person is infected, defaults None.
        recovered_day : int
            The day a person recovers, defaults None.
        death_day : int
            The day a person dies, defaults None.
        others_infected : list
            Holds a list of others infected.
        recent_infections : list
            Holds a list of recent infections (from the last time they infected people).
        age : string
            Is an age range the person belongs to.
        job : string
            Is the job that belongs to the person.
        house_index : int
        isolation_tendencies : float
            How likely a person is to isolate, defaults None.
        case_severity : string
            Case severity of covid when infected, defaults None.
        mask_type : string
            Determines type of mask worn by person, defaults to None.
        has_mask : bool
            Determines if a person will wear a mask or not, defaults to True.
        goodness : float
        days_in_lockdown : int
            Records the number of days a person has been under lockdown.
        """

        self.infected = infected
        self.recovered = recovered
        self.dead = dead
        self.hospitalized = hospitalized
        self.ICU = ICU
        self.quarantined = quarantined
        self.quarantined_day = quarantined_day
        self.infected_day = infected_day
        self.recovered_day = recovered_day
        self.death_day = death_day
        self.others_infected = [] if others_infected is None else others_infected
        self.cure_days = cure_days
        self.recent_infections = recent_infections
        self.vaccinated = vaccinated
        self.vaccine_type = vaccine_type
        self.index = index
        self.age = age
        self.job = job
        self.household = house_index
        self.isolation_tendencies = isolation_tendencies
        self.case_severity = case_severity
        self.mask_type = mask_type
        self.show_symptoms = False
        self.days_until_symptoms = days_until_symptoms
        self.knows_infected = False
        self.will_get_symptoms = False
        self.has_mask = has_mask
        self.virus_type = virus_type
        self.test_day = None
        self.has_cold = False
        self.days_in_lockdown = 0

        # Set the simulaiton object to access the variables
        self.sim_obj = sim_obj
        self.protocol_compliance = self.sim_obj.protocol_compliance

        # Dictionary of sets that stores all the contacts on a given day
        self.all_contacts = {}
        self.personal_contacts = {}

        # Whether this person uses a contact tracing app
        self.has_ct_app = random() < 1  # TODO add the "CT_APP_PROB" variable here

    def __str__(self):
        """Prints the person identifier.
        Useful for debugging purposes.

        Returns
        -------
        : :obj:`string`
        """
        return f"Person #{self.index}"

    def is_infected(self):
        """Method to retrieve if a person is infected. Returns True if infected, False if
        not.

        Returns
        -------
        self.is_infected: :obj:`bool`
        """
        return self.infected

    def is_recovered(self):
        """Method to retrieve if a person is recovered. Returns True if recovered, False if
        not.

        Returns
        -------
        self.is_recovered: :obj:`bool`
        """
        return self.recovered

    def is_dead(self):
        """Method to retrieve if a person is dead. Returns True if dead, False if not.

        Returns
        -------
        self.is_dead: :obj:`bool`
        """
        return self.dead

    def is_quarantined(self):
        """Method to retrieve if a person is quarantined. Returns True if quarantined,
        False if not.

        Returns
        -------
        self.quarantined: :obj:`bool`
        """
        return self.quarantined

    def is_ICU(self):
        """Method to retrieve if a person will go to ICU. Returns True if in ICU,
        False if not.

        Returns
        -------
        self.ICU:`bool`
        """
        return self.ICU

    def is_hospitalized(self):
        """Method to retrieve if a person is hospitalized. Returns True if in hospital,
        False if not.

        Returns
        -------
        self.hospitalized: :obj:`bool`
        """
        return self.hospitalized

    def set_quarantine(self, day):
        """Method to set a person to be in quarantine. Sets the day the quarantine begins to the day inputted.

        Parameters
        ----------
        day: int
            The day in the simulation when a person is put into quarantine.

        Returns
        -------
        self.quarantined: :obj:`bool`
        """

        # Make sure person is not already quarantined.
        if not self.is_quarantined():
            self.quarantined_day = day
            self.quarantined = True
            self.sim_obj.pop.quarantined[self.index] = self.index

        return self.quarantined

    def leave_quarantine(self, day):
        """ Method to determine if a person is done quarantining based on an inputted day.
        Will return True if person is recovered, dead or the inputted day is greater than
        self.sim_obj.quarantine_time.
        Will return False otherwise.

        Parameters
        ----------
        day: int
            The current day in the simulation to check agaisnt the day when a person went into quarantine.

        Returns
        -------
        not self.quarantined: :obj:`bool`
        """

        if self.recovered or self.dead or (day - self.quarantined_day) >= self.sim_obj.quarantine_time:
            self.quarantined = False
            self.show_symptoms = False
            return True
        return False

    def get_quarantine_day(self):
        """Method to retrieve the day a person is put into quarantine.

        Returns
        -------
        self.quarantined_day: :obj:`int`
        """
        return self.quarantined_day

    def update_uninfected_symptomatic(self):
        """Method to randomly infect a person with non COVID19 symptoms or to turn off non COVID19 symptoms.

        Returns
        -------
        self.show_symptoms: :obj:`bool`
        """

        if self.has_cold:
            if random() <= 1 / self.sim_obj.cold_duration_days:
                self.show_symptoms = False
                self.has_cold = False
        elif random() <= self.sim_obj.cold_prob:
            self.show_symptoms = True
            self.has_cold = True
        return self.show_symptoms

    def set_test_day(self, day):
        """Method to set the day a person is tested.

        Parameters
        ----------
        day: int
            The day in the simulation when the person was tested.
        """
        self.test_day = day

    def get_test_day(self):
        """Method to retrieve the day a person is tested.

        Returns
        -------
        self.test_day: :obj:`int`
        """
        return self.test_day

    def has_been_tested_recently(self, day):
        """Method to check if the person has been tested in the quarantine time range.
        If the day is greater than the test day is removed.
        If the person had a cold it is also removed.

        Parameters
        ----------
        day: int
            The current day in the simulation to compare against when the person was tested.

        Returns
        -------
        : :obj:`bool`
            True if the quarantine time range has passed since they have been last tested and False if not.
        """

        if self.test_day is None:
            return False
        elif (day - self.test_day) < self.sim_obj.quarantine_time:
            return True
        else:
            self.test_day = None
            return False

    def check_symptoms(self, day):
        """Method to check a person's symptoms based on if they are infected with COVID19 or a cold.

        Parameters
        ----------
        day: int
            The current day in the simulation to compare against when the person was tested.

        Returns
        -------
        self.show_symptoms: :obj:`bool`
        """

        if ((self.infected
             and self.will_get_symptoms
             and (day - self.infected_day) >= self.days_until_symptoms)
                or self.has_cold):
            self.show_symptoms = True
        else:
            self.show_symptoms = False

        return self.show_symptoms

    def could_be_symptomatic(self):
        """Method to check if the person could be showing symptoms.

        A person could show symptoms if they are infected or if they have a cold.

        Returns
        -------
        could_be_symptomatic : `bool`
            True if the person has the potential for symptoms, False if not.
        """

        return (self.has_cold or self.infected)

    def get_index(self):
        """Method to retrieve the index of a person.

        Returns
        -------
        self.index: :obj:`int`
        """
        return self.index

    def get_others_infected(self):
        """Method to retrieve list of others infected.

        Returns
        -------
        self.other_infected: :obj:`list`
        """
        return self.others_infected

    def get_recent_infections(self):
        """Method to get list of recent infections (from the last time they infected people).

        Returns
        -------
        self.recent_infections: :obj:`list`
        """
        return self.recent_infections

    def get_case_severity(self):
        """Method to retrieve case severity of covid.

        Returns
        -------
        self.case_severity: :obj:`string`
        """
        return self.case_severity

    def get_mask(self):
        """Method to retrieve if a person is wearing a mask.

        Returns
        -------
        self.has_mask: :obj:`bool`
        """
        return self.has_mask

    def get_virus_type(self):
        """Method to return the virus type of a person.

        Returns
        -------
        self.virus_type: :obj:`int`
        """
        return self.virus_type

    def infect(self, day, virus_type, cure_days=None):
        """Method to infect a person.

        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.
        virus_type : str
            The type of virus that this person is being infected with.
        cure_days : int
            The day value set for the person to be cured after being infected.

        Returns
        -------
        : :obj:`bool`
            True if infected and False if not.
        """

        d_params = self.sim_obj.disease_parameters

        # Check that they are suseptable (maybe should have that as property?)
        if not self.recovered and not self.infected and not self.dead:
            self.infected = True
            self.virus_type = virus_type
            self.infected_day = day
            self.will_get_symptoms = True
            self.days_until_symptoms = np.random.randint(d_params["days_before_symptoms"]["min"],
                                                         d_params["days_before_symptoms"]["max"])

            # If cure days not specified then choose random number inbetween min and max
            if self.case_severity == 'Mild' or self.case_severity is None:  # If severity not specified, choose Mild
                if random() > d_params["mild_symptom_prob"]:  # probability that the person has mild symptoms
                    # choose number of days after infection when symptoms show
                    self.will_get_symptoms = False
                    self.days_until_symptoms = None

                self.cure_days = np.random.randint(d_params["mild_days"]["min"],
                                                   d_params["mild_days"]["max"]) if cure_days is None else cure_days
            # Assuming that all hospitalization or worse cases will show symptoms
            elif self.case_severity == 'Hospitalization':
                self.cure_days = np.random.randint(d_params["hospital_days"]["min"],
                                                   d_params["hospital_days"]["max"]) if cure_days is None else cure_days
                self.hospitalized = True
            elif self.case_severity == 'ICU':
                self.cure_days = np.random.randint(d_params["ICU_days"]["min"],
                                                   d_params["ICU_days"]["max"]) if cure_days is None else cure_days
                self.hospitalized = True
                self.ICU = True
            elif self.case_severity == 'Death':
                self.cure_days = np.random.randint(d_params["die_days"]["min"],
                                                   d_params["die_days"]["max"]) if cure_days is None else cure_days
                self.hospitalized = True
                self.ICU = True
            else:
                raise ValueError(f"'{self.case_severity}' is not a valid case severity.")

            return True

        return False

    def check_quarantine(self, day):
        """Method to check if a person should be quarantined.
        If they're quarantined and their quarantine time has ended, let them out of quarantine.
        If they're not quarantined but they have severe symptoms, set self.quarantined to be True.

        Parameters
        ----------
        day : int
            The day value that this function is being called on in the encompassing simulation class.

        Returns
        -------
        : :obj:`bool`
            True if quarantined and False if not.
        """

        if self.quarantined:
            days_since_quarantined = day - self.quarantined_day
            if days_since_quarantined >= self.sim_obj.quarantine_time:
                self.quarantined = False
                self.sim_obj.pop.quarantined[self.index] = -1  # Null value
                return False
            return True
        else:  # if not self quarantined
            # if they aren't in quarantine, check if they know they're infected
            #   then put them into quarantine
            if self.case_severity != "Mild":
                # if their symtoms are not mild, quarantine if they're infected
                # assume people in the hospital aren't spreading it either
                self.set_quarantine(day)

                return True
            return False

    def check_cured(self, day):
        """Method that checks if a person is past their cure time and will cure them
        their days_since_infected is greater or equal to their cure_days.

        Parameters
        ----------
        day : int
            The day value that this function is being called on to check if cured.

        Returns
        -------
        : :obj:`bool`
            True if they were cured, False if not.
        """

        if self.infected and not self.recovered:
            # Checks cure timeline
            days_since_infected = day - self.infected_day
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
                self.ICU = False

                return True

        return False

    def check_dead(self, day):  # checking that case_severity==death outside of the loop
        """Method to check the timeline if a person will be die once they are infected if
        their days_since_infected is greater or equal to their cure_days.

        Parameters
        ----------
        day : int
            The day value that this function is being called on to check if dead.

        Returns
        -------
        : :obj:`bool`
            True they died and False if not.
        """

        if self.infected and self.case_severity == 'Death':
            # Checks death timeline
            days_since_infected = day - self.infected_day
            if days_since_infected >= self.cure_days:
                self.infected = False
                self.dead = True
                self.death_day = day

                return True

        return False

    def check_hospitalized(self):
        """Method to check if a person will be hospitalized or not once they are infected.

        Returns
        -------
        : :obj:`bool`
            True if hospitalized and False if not.
        """

        if self.infected and self.case_severity in ('Hospitalization', 'ICU', 'Death'):
            self.hospitalized = True
            return True

        return False

    def check_ICU(self):
        """Method to check if a person will go to ICU or not once they are infected.

        Returns
        -------
        : :obj:`bool`
            True if person goes to ICU and False if not.
        """

        if self.infected and self.case_severity in ('ICU', 'Death'):
            self.ICU = True
            return True

        return False

    def wear_mask(self):
        """Method to check if a person will wear a mask.

        Returns
        -------
        : :obj:`bool`
            True if wearing a mask and False if not.
        """

        mask_options = np.random.uniform()

        if self.has_mask:
            if mask_options / self.protocol_compliance > self.sim_obj.wear_mask_properly:
                return False  # False = not wearing a mask
            else:
                return True  # True = wearing a mask
        else:
            return False

    def mask_type_efficiency(self):
        """Method to determines what the inward and outward efficiency of the spread will
        be based on the type of mask worn.

        Returns
        -------
        self.sim_obj.mask_inward_eff[self.mask_type]: :obj:`float`
            Mask inward efficiency for the person's mask type.

        self.sim_obj.mask_outward_eff[self.mask_type]: :obj:`float`
            Mask outward efficiency for the person's mask type.
        """

        if self.has_mask:
            try:
                return (self.sim_obj.mask_inward_eff[self.mask_type],
                        self.sim_obj.mask_outward_eff[self.mask_type])
            except KeyError as e:
                raise ValueError((f"'{self.mask_type}' is not a valid mask type "
                                  "and has no associated efficiency.")) from e
        else:
            return 1, 1  # Not wearing a mask, so no change in chance of infection

    def log_contact(self, other, day: int, personal: bool = False) -> None:
        """Logs a contact between two individuals.

        Parameters
        ----------
        other : :obj:`Person`
            Person that self is interacting with.
        day : int
            Current day in the simulation.
        personal : bool, default False
            Whether or not the two people know each other.
        """

        def add_contact(log):
            if day in log.keys():
                log[day].add(other)
            else:
                log[day] = set([other])

        add_contact(self.all_contacts)
        if personal:
            add_contact(self.personal_contacts)

    def contact_tracing(self, day: int) -> None:
        """Contacts everyone that they have had contact with.

        Parameters
        ----------
        day : int
            Current day in the simulation.
        """

        end = day + 1
        beginning = end - self.sim_obj.ct_length

        def get_contacts(log):
            contacts = set()
            for d in range(beginning, end):
                if d in log.keys():
                    contacts = contacts.union(log[d])
            return contacts

        # Personal contacts
        personal_contacts = get_contacts(self.personal_contacts)
        remembered_contacts = set()

        # Notify all personal contacts
        for contact in personal_contacts:
            if random() < self.sim_obj.ct_prob_remember_personal_contacts:
                contact.positive_contact(day)
                remembered_contacts.add(contact)

        # CT apps
        if self.has_ct_app:
            # Gets all contacts that are from the CT app, minus those
            # already contacted because they were personal contacts
            impersonal_contacts = get_contacts(self.all_contacts).difference(remembered_contacts)

            for contact in impersonal_contacts:
                contact.positive_contact(day)

    def positive_contact(self, day):
        """Called when a person is notified of a positive contact with a
        covid case.
        """

        self.set_quarantine(day)

    def set_protocol_compliance(self, house_size):
        """Method to set the initial protocol compliance value of a person.

        Parameters
        ----------
        house_size: int
            Number of people living in said persons house.

        Returns
        -------
        self.protocol_compliance: :obj:`float`
        """

        if not hasattr(self, "protocol_compliance"):  # If no protocol compliance score is defined
            self.protocol_compliance = self.sim_obj.goodness

        if house_size > len(self.sim_obj.protocol_compliance_house_prob):  # Sets the house size to the largest house size probability if the house size is larger than that number
            house_size = len(self.sim_obj.protocol_compliance_house_prob)
        if random() < self.sim_obj.protocol_compliance_house_prob[house_size - 1]:
            self.protocol_compliance *= self.sim_obj.protocol_compliance_house_reduction[house_size - 1]  # changes the persons protocol compliance based on house size

        if random() < self.sim_obj.protocol_compliance_age_prob[self.age]:
            self.protocol_compliance *= self.sim_obj.protocol_compliance_age_reduction[self.age]

        if random() < self.sim_obj.protocol_compliance_case_severity_prob[self.case_severity]:
            self.protocol_compliance *= self.sim_obj.protocol_compliance_case_severity_reduction[self.case_severity]  # changes protocol compliance based on how severity of a potential case
        return self.protocol_compliance

    def update_protocol_compliance(self, lockdown_level, old_lockdown_mandate):
        """Method to update the protocol compliance value of a person.

        Parameters
        -------
        lockdown_level: bool
            Paramter to check if the lockdown is on (True).
        old_lockdown_mandate: bool
            Paramter to check what the lockdown was the day before the current one.

        Returns
        -------
        self.protocol_compliance: :obj:`float`
        """

        # If no protocol compliance it is defined
        if not hasattr(self, "protocol_compliance"):
            self.protocol_compliance = self.sim_obj.protocol_compliance

        # As the lockdown length increases, decrease the protocol compliance
        if self.days_in_lockdown > self.sim_obj.protocol_compliance_lockdown_length_threshold and random() < self.sim_obj.protocol_compliance_lockdown_prob:
            self.protocol_compliance *= self.sim_obj.protocol_compliance_lockdown_length_reduction

        if lockdown_level != old_lockdown_mandate:
            # when the lockdown starts increase the protocol compliance of a person
            if lockdown_level and random() < self.sim_obj.protocol_compliance_lockdown_prob:
                self.protocol_compliance *= self.sim_obj.protocol_compliance_lockdown_reduction
            # when the lockdown ends decrease the protocol compliance of a person
            elif not lockdown_level and random() < self.sim_obj.protocol_compliance_lockdown_prob:
                self.protocol_compliance /= self.sim_obj.protocol_compliance_lockdown_reduction

        return self.protocol_compliance

    def get_protocol_compliance(self):
        """Method to retrieve the protocol compliance value of a person.

        Returns
        -------
        self.protocol_compliance: :obj:`float`
        """
        return self.protocol_compliance

    def update_lockdown_days(self, lockdown_level):
        """Method to change the number of days a person is in a lockdown or quarantine.

        Returns
        -------
        self.days_in_lockdown: :obj:`int`
        """

        if lockdown_level or self.quarantined:
            self.days_in_lockdown += 1
        elif self.days_in_lockdown != 0:
            self.days_in_lockdown -= 1
        return self.days_in_lockdown

    def is_vaccinated(self):
        """Method to retrieve if a person is vaccinated. Returns True if vaccinated, False if not.

        Returns
        -------
        self.vaccinated: :obj:`bool`
        """
        return self.vaccinated

    def set_vaccinated(self, day):
        """Method to set a person to be vaccinated.

        Parameters
        ----------
        day: int
            The day in the simulation when a person is vaccinated.

        Returns
        -------
        self.vaccinated: :obj:`bool`
        """
        # Make sure person is not already vaccinated.
        if not self.is_vaccinated():
            self.vaccinated_day = day
            self.vaccinated = True

    def vaccine_type_efficiency(self):
        """Method to determines what the efficiency of the vaccine based on the type of vaccine administered.

        Returns
        -------
        self.sim_obj.vaccine_eff[self.vaccine_type]: :obj:`float`
        """
        if self.vaccinated:
            try:
                return self.sim_obj.vaccine_eff[self.vaccine_type]
            except KeyError as e:
                raise ValueError((f"'{self.vaccine_type}' is not a valid vaccine type "
                                  "and has no associated efficiency.")) from e
        else:
            return 1
