import numpy as np
import random

class Person(object):


    def __init__(self, index, sim_obj, infected=False, recovered=False, dead=False, hospitalized=False, quarantined=False,
                 quarantined_day=None, infected_day=None, recovered_day=None, death_day=None, others_infected=None,
                 cure_days=None, recent_infections=None, age=None, job=None, house_index=0, isolation_tendencies=None,
                 case_severity=None, mask_type=None, has_mask=True, virus_type=None):

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
        self.virus_type = virus_type
        
        # Set the simulaiton object to access the variables
        self.sim_obj = sim_obj
        
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
            return True
        return False

    def get_quarantine_day(self):
        return self.quarantined_day
    
    def not_infected_symptoms(self):
        prob_of_symptom = random.random()
        if (prob_of_symptom <= self.sim_obj.cold_prob):
            self.show_symptoms = True
        return self.show_symptoms
            
    
    #checks to see if person shows symptoms on the current day
    def check_symptoms (self,day):
        if (self.will_get_symptoms == True and (day - self.infected_day) >= self.days_until_symptoms
            and self.infected == True):
            self.show_symptoms = True
        elif(self.infected == False):
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
    
    def get_virus_type(self):
        return self.virus_type

    # Method to infect a person
    def infect(self, day, cure_days=None):

        # Check that they are suseptable (maybe should have that as property?)
        if not self.recovered and not self.infected and not self.dead:
            self.infected = True
            #self.virus_type = virus_type
            self.infected_day = day
            self.will_get_symptoms = True
            self.days_until_symptoms  = np.random.randint(self.sim_obj.min_day_before_symptoms, 
                                                          self.sim_obj.max_day_before_symptoms)
            
            # If cure days not specified then choose random number inbetween min and max
            if self.case_severity == 'Mild' or self.case_severity == None: # If severity not specified, choose Mild
                prob_of_symptom = random.random()
                if (prob_of_symptom > self.sim_obj.mild_symptom_prob): #probability that the person has mild symtoms
                    # choose number of days after infection when symptoms show
                    self.will_get_symptoms = False
                    self.days_until_symptoms = None

                self.cure_days = np.random.randint(self.sim_obj.min_mild_days, 
                                                   self.sim_obj.max_mild_days) if cure_days is None else cure_days
            #Assuming that all hospitalization or worse cases will show symptoms
            elif self.case_severity == 'Hospitalization':
                self.cure_days = np.random.randint(self.sim_obj.min_severe_days, 
                                                   self.sim_obj.max_severe_days) if cure_days is None else cure_days
                self.hospitalized = True
            elif self.case_severity == 'ICU':
                self.cure_days = np.random.randint(self.sim_obj.min_ICU_days, 
                                                   self.sim_obj.max_ICU_days) if cure_days is None else cure_days
                self.hospitalized = True
            elif self.case_severity == 'Death':
                self.cure_days = np.random.randint(self.sim_obj.min_die_days, 
                                                   self.sim_obj.max_die_days) if cure_days is None else cure_days
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