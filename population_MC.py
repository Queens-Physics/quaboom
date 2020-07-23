import numpy as np
import Person
import Population

def RunEpidemic(nPop, n0, nDays, contacts_mean, contacts_std, prob_infection):
    #Initialize the population
    pop = Population.Population(nPop, n0)
    
    #Arrays to store the values during the simulation                   
    track_new_infected = np.zeros(nDays, dtype=int) #new infections 
    track_infected = np.zeros(nDays, dtype=int) # currently infected 
    track_susceptible = np.zeros(nDays, dtype=int) # never been exposed
    track_recovered = np.zeros(nDays, dtype=int) #total recovered
    
    #Loop over the number of days
    for day in range(nDays):

        track_infected[day] = pop.count_infected()
        track_susceptible[day] = pop.count_susceptible()
        track_recovered[day] = pop.count_recovered()
        if day != 0:
            new_recovered = track_recovered[day] - track_recovered[day-1]
            track_new_infected[day] = track_infected[day] - track_infected[day-1] + new_recovered
        
        # Itterate through all infected people
        infected_people = pop.get_infected()
        for index in infected_people: 
            infected_person = pop.get_person(index=index)
            
            #Randomly draw a number of contacts that this person will have
            ncontacts = abs(round(np.random.normal(contacts_mean,contacts_std)))
            #Factor in the probability that they will infect those contacts:
            new_infections = round(ncontacts*prob_infection)
            
            if new_infections > 0:
                # Try to infect those people - func will actually change person stats to infected
                actual_new_infections = infected_person.infect_others(pop_list=pop.get_population(),
                                                                      suscept_pop=pop.get_susceptible(), day=day,
                                                                      num_to_infect=new_infections)
                # If there were suscept people to infect:
                if actual_new_infections>0:
                    for new_infection in infected_person.get_recent_infections():
                        # Only need to update population object, as person is already updated by infect_others
                        if pop.update_infected(index=new_infection) == False:
                            print("Did not infect correctly")
                    
            #Check if this person has been sick for long enough to be cured (if yes, cure them!)
            is_cured = infected_person.check_cured(day) # method will check and cure them 
            if is_cured and pop.update_cured(index=infected_person.get_index()) == False:
                print("Did not cure correctly")

        print("Day: {}, infected: {}, recovered: {}, suceptible: {}".format(day, track_infected[day], track_recovered[day],
                                                                            track_susceptible[day]))
    print("At the end, ", track_susceptible[-1], "never got it")
    print(np.max(track_infected), "had it at the peak")
    
    return track_infected, track_new_infected, track_recovered, track_susceptible, Population

