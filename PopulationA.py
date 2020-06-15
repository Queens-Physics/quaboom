
# coding: utf-8

# https://github.com/ArroyoAndre/covidsimulation - found age distribution, isolation and home prob techniques to try to incorperate into our model.

# In[4]:


import numpy as np
import Person


# In[24]:


#adding in random probability of age distributions/ can easily be altered
age_distribution = {
    '0-9': 0.1,
    '10-19': 0.15,
    '20-29': 0.15,
    '30-39': 0.15,
    '40-49': 0.15,
    '50-59': 0.1,
    '60-69': 0.1,
    '70-79': 0.06,
    '80-89': 0.03,
    '90+': 0.01,
}
assert sum(age_distribution.values()) ==1.0 #sum to 100% of the pops ages - will only run if this is true

#adding in random probability of isolation tendencies based on age group
isolation_tendencies = { #implementing the likeliness of infectin others/ random inputs again
    1.0,    #0-9
    1.0,    #10-19
    -0.5,   #20-29 less concerned and may be more essential workers
    -0.5,   #30-39
    0.0,    #40-49
    0.3,    #50-59
    0.8,    #60-69
    1.8,    #70-79
    1.8,    #80-89 old people will isolate better in theory
    3,      #90+
}

#adding in random probabilities of living in a house with x amount of people
#25% of people live alone, 30% have 2 people... again random
home_size_prob = np.array([0.25,0.30,0.30,0.10,0.05])
assert home_size_prob.sum() == 1.0 #sum to 100% of the populations people


# In[25]:


class Population(object):
    
    #Initalize a person - Set properties
    def __init__(self, nPop, age_distribution, home_size_prob,isolation_tendencies): 
        
        self.nPop=[] #empty list for the population
        self.age_distribution = np.array(list(age_distribution.values()))
        self.home_size_prob = home_size_prob #prob of home sizes
        self.isolation_tendencies = isolation_tendencies
        
        #adding new variables to the Person class
        for i in range(0,nPop):
            age_distribution = np.array(list(age_distribution.values()))
            home_size_prob = home_size_prob
            isolation_tendencies = isolation_tendencies
            NewPerson = Person(i+1,False,False,None,None,None,None,None,age_distribtion,home_size_prob,isolation_tendencies)
            self.nPop.append(NewPerson)
            
    #method to initialize the population
    def init_pop(self,inital_infections):
        
        self.inital_infections = 1
        
        for i in np.arange(0,int(self.inital_infections)): #inital infections = 1
            self.infected

        for i in np.arange(0,self.nPop - intial_infections): #inital susceptible
            self.susceptible
            
    def get_population(self):
        return self.nPop  #return: a list with the current person instances

    def set_population(self, pop):
        self.nPop = pop #update the pop in the current iteration *something to add when we account for people dying
    
    #Method checks if a person is still infected/ same as check_cured in person.py but with opposite signs to check infected
    def check_infected(self):
        if self.infected and not self.recovered:
            days_since_infected = day - self.infected_day
            if days_since_infected <= self.cure_days:
                self.infected = True
                self.recovered = False
                return True
        return False
            
        return self.infected
        
    def check_cured(self):
        return self.recovered

