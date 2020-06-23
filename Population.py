import Person
import random

class Population:
    
    '''creates a population of people based on the total population
     uses and age distrubution to weight the assignment of ages'''
    def __init__(self,nPop,n0,ageDistrubution,jobDistrubution,householdDistribution,isolationArray):
        
        self.list = [] #The list of all people
        self.suceptible = []
        self.infected = [] #list of all infected people
        self.recovered = []
        self.household = []
        self.pop = nPop

        for i in range (0,self.pop):
            
            Age = (['0-9']*ageDistrubution[0] + ['10-19']*ageDistrubution[1] 
                   + ['20-29']*ageDistrubution[2] + ['30-39']*ageDistrubution[3] 
                   + ['40-49']*ageDistrubution[4] + ['50-59']*ageDistrubution[5] 
                   + ['60-69']*ageDistrubution[5] + ['70-79']*ageDistrubution[6] 
                   + ['80-89']*ageDistrubution[7] + ['90+']*ageDistrubution[8])
            age = random.choice(Age)
            
            if age == '0-9':      
                isolation_tendencies = isolationArray[0]
            elif age == '10-19':
                isolation_tendencies = isolationArray[1]
            elif age == '20-29' :
                isolation_tendencies = isolationArray[2]
            elif age == '30-39':
                isolation_tendencies = isolationArray[3]
            elif age == '40-49':
                isolation_tendencies = isolationArray[4]
            elif age == '50-59':
                isolation_tendencies = isolationArray[5]
            elif age == '60-69':
                isolation_tendencies = isolationArray[6]
            elif age == '70-79':
                isolation_tendencies = isolationArray[7]
            elif age == '80-89':
                isolation_tendencies = isolationArray[8]
            elif age == '90+':
                isolation_tendencies = isolationArray[9]
            else:
                isolation_tendencies = 1
            
            
            #Job = ['Essential'] * jobDistrubution[0] + ['Commercial'] * jobDistrubution[1]
            
            NewPerson = Person(i,False,False,None,None,None,None,None,age,0,isolation_tendencies)
            self.list.append(NewPerson)  #adds new person to list
        
        #Creation of the households 
        n = 0
        tempList = len(self.list) # creates a temporary list
        for i in range (0,len(self.list)):
             if (tempList > 0):
                HousePopProb = (['1'] * householdDistribution[0] + ['2'] * householdDistribution[1]
                + ['3'] * householdDistribution[2] + ['4'] * householdDistribution[3] + ['5'] * householdDistribution[4]
                + ['6'] * householdDistribution[5])
                HousePop = int(random.choice(HousePopProb))
            
                for f in range (0,HousePop):
                    if (tempList > 0): 
                        self.list[i].set_house(n)
                        tempList = tempList - 1
                n = n + 1
        
        
        self.suceptible = self.list

        #infects the initial people
        for i in range(n0):
            self.list[i].infect(day=0)
            self.infected.append(self.list[i])
            self.suceptible.pop(i)
            
    def get_population(self):
        return self.nPop
    # counts the total number of suceptible individuals
    def count_suceptible(self):
        suceptiple_population = len(self.suceptible)
        return suceptiple_population
    
    def check_individual(self,index): 
        return self.list[index]
    
    # returns the list of suceptible  individuals
    def check_suceptible(self):
        return self.suceptible

    #counts the total number of infected individuals
    def count_infected(self):
        infected_population = len(self.infected)
        return infected_population

    #returns the list of infected individuals
    def check_infected(self):
        for i in range(len(self.suceptible)):
            if (obj.is_infected for obj in self.suceptible):
                self.infected.append(self.suceptible[i])
                self.suceptible.pop(i)
        return self.infected

    #counts the total number of recovered individuals
    def count_recovered(self):
        recovered_population = len(self.recovered)
        return recovered_population

    def check_recoverd(self):
        return self.recovered
