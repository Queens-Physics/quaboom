import numpy as np
class Person:
    
    # Initalize a person - Can set properties but only needed one is index
    def __init__(self, index, infected=False, recovered=False, infected_day=None, recovered_day=None, 
                 others_infected=None, cure_days=None, recent_infections=None):
        
        self.infected = infected
        self.recovered = recovered
        self.infected_day = infected_day
        self.recovered_day = recovered_day
        self.others_infected = [] if others_infected is None else others_infected
        self.cure_days = cure_days
        self.recent_infections = recent_infections
        self.index = index
        
    # Return True if infected, False if not
    def is_infected(self):
        if self.infected:
            return True
        else:
            return False
    
    # Return True if recovered, False if not
    def is_recovered(self):
        if self.recovered:
            return True
        else:
            return False
    
    # Return index of person
    def get_index(self):
        return self.index
    
    # Return list of others infected
    def get_others_infected(self):
        return self.others_infected
    
    # Get list of recent infections (from the last time they infected people)
    def get_recent_infections(self):
        return self.recent_infections
    
    # Method to infect a person
    def infect(self, day, cure_days=None):
        
        # Check that they are suseptable (maybe should have that as property?)
        if not self.recovered and not self.infected:
            self.infected = True
            self.infected_day = day
            # If cure days not specified then choose random number inbetween 10 and 20
            if cure_days is None:
                self.cure_days = np.random.randint(10, 20)
                
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
                
                return True
        return False
    
    # Method to infect a random subset of the susceptable population. Returns how many people infected
    def infect_others(self, pop_list, suscept_pop, day, num_to_infect=1):
        
        # If there are no susceptable people, return 0 infections
        if len(suscept_pop) == 0:
            return 0
            
        # Choose the ranom indices from the population to have infectious contacts with
        infect_indexs = np.random.choice(len(pop_list), num_to_infect, replace=False)
        actual_infections = []
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
            actual_infections.append(person_index)
            
        # Update 
        self.recent_infections = actual_infections

        return len(actual_infections)
    
    
    
    
    
    
    
        
