import numpy as np
import Person
import Population
import Interaction_Sites

# will_go_to_site parameters (prob person will go somewhere each day) 
A_WILL_GO_PROB = .05
B_WILL_GO_PROB = .4
C_WILL_GO_PROB = .8

def RunEpidemic(nPop, n0, nDays):
    # Initialize the population
    pop = Population.Population(nPop, n0)
    
    # Initalize the interaction sites
    inter_sites = Interaction_Sites.Interaction_Sites(pop_obj=pop)
    
    # Arrays to store the values during the simulation                   
    track_new_infected = np.zeros(nDays, dtype=int) #new infections 
    track_infected = np.zeros(nDays, dtype=int) # currently infected 
    track_susceptible = np.zeros(nDays, dtype=int) # never been exposed
    track_recovered = np.zeros(nDays, dtype=int) #total recovered
    
    # Loop over the number of days
    for day in range(nDays):

        #Count all the different states of people
        track_infected[day] = pop.count_infected()
        track_susceptible[day] = pop.count_susceptible()
        track_recovered[day] = pop.count_recovered()
        if day != 0:
            new_recovered = track_recovered[day] - track_recovered[day-1]
            track_new_infected[day] = track_infected[day] - track_infected[day-1] + new_recovered
            
        # Find grade A, B, C site visits
        will_visit_A = inter_sites.will_visit_site(inter_sites.get_grade_A_sites(), A_WILL_GO_PROB)
        will_visit_B = inter_sites.will_visit_site(inter_sites.get_grade_B_sites(), B_WILL_GO_PROB)
        will_visit_C = inter_sites.will_visit_site(inter_sites.get_grade_C_sites(), C_WILL_GO_PROB)
        
        # Do site interactions based on who is going to sites - INFECTION SPREAD OCCURS HERE
        inter_sites.site_interaction(pop, will_visit_A, inter_sites.get_grade_A_sites(), day)
        #inter_sites.site_interaction(pop, will_visit_B, inter_sites.get_grade_B_sites(), day)
        #inter_sites.site_interaction(pop, will_visit_C, inter_sites.get_grade_C_sites(), day)
        
        # Manage at home interactions
        inter_sites.house_interact(pop, day)  
        
        # See who needs to be cured
        infected_people = pop.get_infected()
        for index in infected_people: 
            infected_person = pop.get_person(index=index) 
            is_cured = infected_person.check_cured(day) # method will check and cure them if needed
            if is_cured and pop.update_cured(index=infected_person.get_index()) == False:
                print("Did not cure correctly")


        print("Day: {}, infected: {}, recovered: {}, suceptible: {}".format(day, track_infected[day], track_recovered[day],
                                                                            track_susceptible[day]))
    print("At the end, ", track_susceptible[-1], "never got it")
    print(np.max(track_infected), "had it at the peak")
    
    return track_infected, track_new_infected, track_recovered, track_susceptible, Population

