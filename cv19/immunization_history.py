class ImmunizationHistory:
    '''
    A class designed to keep track of a Person's vaccination history and vaccination parameters.

    Holds the parameters from immunization_history.toml corresponding to the Person's vaccine type,
    as well as the attributes listed below.

    Attributes
    ----------
    vaccinated: :obj:`bool`
        A variable indicating whether or not the person is vaccinated.
    list_of_vaccination_dates: :obj:`list` of int
        A list of a Person's vaccination dates (corresponding to day in simulation).
    '''

    def __init__(self, vaccine_type=None, vaccine_max_efficacy=None, vaccine_immunity_buildup_days=None, long_term_vaccine_eff=None, vaccine_efficacy_min_day=None):
        '''
        The constructor for the Immunization History class.
        '''

        self.vaccinated = False
        self.list_of_vaccination_dates = list()
        self.vaccine_type = vaccine_type
        self.vaccine_max_efficacy = vaccine_max_efficacy
        self.vaccine_immunity_buildup_days = vaccine_immunity_buildup_days
        self.long_term_vaccine_eff = long_term_vaccine_eff
        self.vaccine_efficacy_min_day = vaccine_efficacy_min_day

    def is_vaccinated(self):
        '''Method to retrieve if a person is vaccinated. Returns True if vaccinated, False if not.

        Returns
        -------
        self.vaccinated: :obj:`bool`
        '''
        return self.vaccinated

    def set_vaccinated(self, day):
        '''Method to set a person to be vaccinated.

        Parameters
        ----------
        day: int
            The day in the simulation when a person is vaccinated.

        Returns
        -------
        self.vaccinated: :obj:`bool`
        '''
        self.vaccinated_day = day
        self.list_of_vaccination_dates.append(self.vaccinated_day)
        self.vaccinated = True

    def vaccine_efficacy(self, day):
        '''Method to determine what the efficiency of the vaccine based on the type of vaccine administered, and other
        immunization history parameters.

        Returns
        -------
        self.current_vax_eff: :obj:`float`
        '''

        if self.vaccinated:

            days_since_vaccination = day - self.list_of_vaccination_dates[-1]
            if days_since_vaccination == 0:
                self.current_vaccine_eff = 0
            elif days_since_vaccination <= self.vaccine_immunity_buildup_days:  # linear increase of immunity
                self.current_vaccine_eff = ((self.vaccine_max_efficacy) / (self.vaccine_immunity_buildup_days)) * days_since_vaccination
            elif (days_since_vaccination > self.vaccine_immunity_buildup_days) and (days_since_vaccination < self.vaccine_efficacy_min_day):  # calculate linearly decreasing immunity
                self.current_vaccine_eff = (-(self.vaccine_max_efficacy - self.long_term_vaccine_eff) / (self.vaccine_efficacy_min_day - self.vaccine_immunity_buildup_days))  # slope calculation
                self.current_vaccine_eff *= days_since_vaccination  # scale by days since vaccination
                self.current_vaccine_eff += self.vaccine_max_efficacy  # add initial value (which is the max efficacy)
            else: # plateau in immunity after and including min_day
                self.current_vaccine_eff = self.long_term_vaccine_eff

            return self.current_vaccine_eff

        else:
            return 0
