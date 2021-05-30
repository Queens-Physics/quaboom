import numpy as np
import random
import json

TIME_QUARANTINE = 14 #days people have to quarantine
Surgical_Inward_Eff = 0.4
Surgical_Outward_Eff = 0.3
NonSurgical_Inward_Eff = 0.6
NonSurgical_Outward_Eff = 0.5

# How long the infection will last
json_file = open('dataK.json')
disease_params = json.load(json_file)

# recovery
MIN_MILD= disease_params['recovery'][0]['MIN_MILD']
MAX_MILD= disease_params['recovery'][0]['MAX_MILD']
MIN_SEVERE= disease_params['recovery'][0]['MIN_SEVERE']
MAX_SEVERE= disease_params['recovery'][0]['MAX_SEVERE']
MIN_ICU= disease_params['recovery'][0]['MIN_ICU']
MAX_ICU= disease_params['recovery'][0]['MAX_ICU']
MIN_DIE= disease_params['recovery'][0]['MIN_DIE']
MAX_DIE= disease_params['recovery'][0]['MAX_DIE']

MASKPROB = 0.8 #Probability of wearing a mask properly
MILD_SYMPTOM_PROB = 0.8 # Probability of mild symptoms
MIN_DAY_BEFORE_SYMPTOM, MAX_DAY_BEFORE_SYMPTOM = 1, 10
QUARANTINE_TIME = 14
CHANCE_OF_COLD = 0.02 #probability of getting a cold or flu during quarantine

#### Contact Tracing Variables

# Probability [0, 1] that a person has a contact tracing app
CT_APP_PROB = 1

# Proportion of personal contacts [0, 1] that are remembered when it's time
# to do contact tracing
PROB_REMEMBERING_PERSONAL_CONTACTS = 0.75

# How many days in the past to contact trace to
CT_LENGTH = 2

json_file.close()

class Person(object):

    

    # Initalize a person - Can set properties but only needed one is inde
    def __init__(self, index, infected=False, recovered=False, dead=False, hospitalized=False, quarantined=False, quarantined_day=None, 
                 infected_day=None, recovered_day=None, death_day=None, others_infected=None, cure_days=None, 
                 recent_infections=None, age=None, job=None, house_index=0,isolation_tendencies=None,case_severity=None, mask_type=None, 
                 has_mask=True):


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

        #### CONTACT TRACING INFO ####
        # Dictionary of sets that stores all the contacts on a given day
        self.all_contacts = dict()
        self.personal_contacts = dict()
        
        # Whether the person uses a contact tracing app
        self.has_ct_app = random.random() < CT_APP_PROB

        self.test_day = None
        self.has_cold = False
        
        # Set the simulaiton object to access the variables
        self.sim_obj = sim_obj

        
    def __repr__(self):
        return f"Person #{self.index}"

    # Return True if infected, False if not
    def is_infected(self):
        return self.infected

    # Return True if recovered, False if not
    def is_recovered(self):
        return self.recovered

    #return True if dead, False if not
    def is_dead(self):
        return self.dead

    #return True if quarantined, False if not
    def is_quarantined(self):
        return self.quarantined
    
    def is_hospitalzied(self):
        return self.hospitalized

    #Puts person in quarantine
    def set_quarantine(self,day):
        self.quarantined_day = day
        self.quarantined = True

    #Allows recovered individuals to leave quarantine
    def leave_quarantine(self, day):
        if self.quarantined_day == None: 
            self.quarantined_day = 0
        if self.recovered == True or self.dead == True or (day - self.quarantined_day) >= self.sim_obj.quarantine_time:
            self.quarantined = False
            self.show_symptoms = False
            return True
        return False

    def get_quarantine_day(self):
        return self.quarantined_day
    
    def not_infected_symptoms(self):
        prob_of_symptom = random.random()
        if prob_of_symptom <= self.sim_obj.cold_prob:
            self.show_symptoms = True
            self.has_cold = True
        return self.show_symptoms
          
    def set_test_day(self,day): 
        self.test_day = day
    
    def get_test_day(self): 
        return self.test_day
    
    def check_test_day (self, day): 
        if self.test_day is None: 
            return False
        elif (day - self.test_day) >= self.quarantine_time: 
            self.test_day = None
            self.has_cold = False
            return True
        return False
    
    #checks to see if person shows symptoms on the current day
    def check_symptoms (self,day):
        if self.will_get_symptoms == True and (day - self.infected_day) >= self.days_until_symptoms and self.infected == True or self.has_cold:
            self.show_symptoms = True
        elif(self.infected == False and self.has_cold == False):
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
            if self.case_severity == 'Mild' or self.case_severity == None: # If severity not specified, choose Mild
                prob_of_symptom = random.random()
                if (prob_of_symptom > d_params["mild_symptom_prob"]): #probability that the person has mild symtoms
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
        else: # if not self quarantined
            # if they aren't in quarantine, check if they know they're infected
            ##   then put them into quarantine
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
    
    def check_hospitalized(self, day): # checking that case_severity==death outside of the loop
        if self.infected:
            if self.case_severity == 'Hospitalization' or self.case_severity == 'ICU' or self.case_severity == 'Death':
                self.hospitalized = True

            return True
        return False

    def wear_mask(self): #Determines and returns if person is wearing mask
        mask_options = np.random.uniform()
        
        if self.has_mask:
            if mask_options > self.sim_obj.wear_mask_properly:
                return False #False = not wearing a mask
            else:
                return True #True = wearing a mask
        else:
            return False
    
    #Determines what the inward and outward efficiency of the spread will be based on the mask they are wearing
    def mask_type_efficiency(self):
        if self.has_mask == True and self.mask_type == "Surgical":
            return self.sim_obj.surgical_inward_eff, self.sim_obj.surgical_outward_eff
        elif self.has_mask == True and self.mask_type == "Non-surgical":
            return self.sim_obj.nonsurgical_inward_eff, self.sim_obj.nonsurgical_outward_eff
        else:
            return 1, 1 #Not wearing a mask so this will function will not effect their change of getting the virus
        
    # Method to infect a random subset of the susceptable population. Returns how many people infected
    def infect_others(self, pop_list, suscept_pop, day, num_to_infect=1):

        # If there are no susceptable people, return 0 infections
        if len(suscept_pop) == 0:
            return 0

        # Choose the random indices from the population to have infectious contacts with
        contact_options = list(range(len(pop_list)))
        contact_options.remove(self.index)       # Make it so that it can not select itself as a contact
        infect_indexs = np.random.choice(contact_options, num_to_infect, replace=False)
        self.recent_infections = []
        infectCount = 0
        for index in infect_indexs:
            # If the contact was not susceptable, nothing happens
            if index not in suscept_pop:
                continue

            # Get the id of the susceptable person being infected
            person_to_infect = pop_list[index]
            person_index = person_to_infect.get_index()

            # Infect that person
            person_to_infect.infect(day)

            # Update others infected list
            self.others_infected.append(person_index)
            # Update who was actually infected
            self.recent_infections.append(person_index)

        return len(self.recent_infections)


    #### CONTACT TRACING FUNCTIONS ####

    def log_contact(self, other, day: int, personal: bool = False) -> None:
        """Logs a contact between two individuals. """

        def add_contact(log):
            if day in log.keys():
                log[day].add(other)                
            else:
                log[day] = set([other])

        add_contact(self.all_contacts)
        if personal:
            add_contact(self.personal_contacts)
        

    def contact_tracing(self, day: int) -> None:
        """Contacts everyone that they have had contact with. """

        end = day + 1
        beginning = end - CT_LENGTH
        
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
            if random.random() < PROB_REMEMBERING_PERSONAL_CONTACTS:
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
        '''Called when a person is notified of a positive contact with a
        covid case. '''

        #NOTE: This is a pretty intense course of action. Maybe adding them to
        # the testing list would be better?
        self.set_quarantine(day)        

