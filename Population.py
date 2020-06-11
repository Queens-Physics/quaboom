import Person
import random

class Population:
    '''creates a population of people based on the total population
     uses and age distrubution to weight the assignment of ages'''
    def __init__(self,nPop,ageDistrubution):
        self.list = [] #The list of all people
        for i in range (0,nPop):
            Age = ['1'] * ageDistrubution[0] + ['30'] * ageDistrubution[1] + ['80'] * ageDistrubution[2]
            age = int((random.choice(Age))) #chooses a weighted random age from above and converts the string to int
            NewPerson = Person(i+1,False,False,None,None,None,None,None,age)
            self.list.append(NewPerson)  #adds new person to list

    #counts the total number of infected individuals
    def check_infected(self):
        infected_population = sum(obj.infected == True for obj in self.list)
        return infected_population

    #counts the total number of recovered individuals
    def check_recovered(self):
        recovered_population = sum(obj.recovered == True for obj in self.list)
        return recovered_population

