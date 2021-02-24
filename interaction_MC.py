import numpy as np
import Person
import Population
import Interaction_Sites
import Policy

# will_go_to_site parameters (prob person will go somewhere each day)
A_WILL_GO_PROB = .05
B_WILL_GO_PROB = .4
C_WILL_GO_PROB = .8
TESTS_PER_DAY = 100

# Polciy variables
initial_mask_mandate, initial_lockdown_mandate = False, False
lockdown_trigger, lockdown_day_trigger = None, 25
mask_trigger, mask_day_trigger = None, 25

def RunEpidemic(nPop, n0, nDays):
    # Initalize the policy class
    policy = Policy.Policy(initial_mask_mandate=initial_mask_mandate, initial_lockdown_mandate=initial_lockdown_mandate, 
                           mask_trigger=mask_trigger, mask_day_trigger=mask_day_trigger, 
                           lockdown_trigger=lockdown_trigger, lockdown_day_trigger=lockdown_day_trigger)
    
    old_mask_mandate, old_lockdown = initial_mask_mandate, initial_lockdown_mandate
    
    # Initialize the population
    pop = Population.Population(nPop, n0, policy=policy)
    
    # Initalize the interaction sites
    inter_sites = Interaction_Sites.Interaction_Sites(pop_obj=pop, policy=policy)
    
    # Link the pop and inter_sites to the policy class
    policy.set_simulation(population=pop, interaction_sites=inter_sites)

    # Arrays to store the values during the simulation
    track_new_infected = np.zeros(nDays, dtype=int) # new infections
    track_infected = np.zeros(nDays, dtype=int)     # currently infected
    track_susceptible = np.zeros(nDays, dtype=int)  # never been exposed
    track_recovered = np.zeros(nDays, dtype=int)    # total recovered
    track_dead = np.zeros(nDays, dtype=int)         # total deaths
    track_tested = np.zeros(nDays, dtype=int)       # total tested individuals
    track_quarantined = np.zeros(nDays, dtype=int)  # population currently in quarantine ACTUALLY DOES TOTAL QUARINTIED 

    # Loop over the number of days
    for day in range(nDays):

        #Count all the different states of people
        track_infected[day] = pop.count_infected()
        track_susceptible[day] = pop.count_susceptible()
        track_recovered[day] = pop.count_recovered()
        track_dead[day] = pop.count_dead()
        track_tested[day] = pop.count_tested()
        track_quarantined[day] = pop.count_quarantined()

        #track the days someone has been infected?
        if day != 0:
            new_recovered = track_recovered[day] - track_recovered[day-1]
            new_dead = track_dead[day] - track_dead[day-1]
            track_new_infected[day] = track_infected[day] - track_infected[day-1] + new_recovered + new_dead

        # Find grade A, B, C site visits
        will_visit_A = inter_sites.will_visit_site(inter_sites.get_grade_A_sites(), A_WILL_GO_PROB)
        will_visit_B = inter_sites.will_visit_site(inter_sites.get_grade_B_sites(), B_WILL_GO_PROB)
        will_visit_C = inter_sites.will_visit_site(inter_sites.get_grade_C_sites(), C_WILL_GO_PROB)

        # Do site interactions based on who is going to sites - INFECTION SPREAD OCCURS HERE
        inter_sites.site_interaction(will_visit_A, inter_sites.get_grade_A_sites(), day)
        #inter_sites.site_interaction(will_visit_B, inter_sites.get_grade_B_sites(), day)
        #inter_sites.site_interaction(will_visit_C, inter_sites.get_grade_C_sites(), day)

        # Manage at home interactions
        inter_sites.house_interact(day)

        #Manage testing sites
        inter_sites.testing_site(TESTS_PER_DAY, day)

        # See who needs to be cured or die
        infected_people = pop.get_infected()
        for index in infected_people:
            infected_person = pop.get_person(index=index)

            if infected_person.get_case_severity() == "Death":
                is_dead = infected_person.check_dead(day)
                if is_dead and pop.update_dead(index=infected_person.get_index()) == False:
                    print("Did not die correctly")

            else:
                is_cured = infected_person.check_cured(day) # method will check and cure them if needed ALWAYS IS FALSE??
                if is_cured and pop.update_cured(index=infected_person.get_index()) == False:
                    print("Did not cure correctly")

                is_quarantined = infected_person.check_quarantine(day)

        print("Day: {}, infected: {}, recovered: {}, suceptible: {}, dead: {}, tested: {} total quarantined: {}".format(day, track_infected[day],
                                                                                      track_recovered[day],
                                                                                      track_susceptible[day],
                                                                                      track_dead[day],
                                                                                      track_tested[day],
                                                                                      track_quarantined[day]))
    print("At the end, ", track_susceptible[-1], "never got it")
    print(track_dead[-1], "died")
    print(np.max(track_infected), "had it at the peak")
    print(track_tested[day], "have been tested")
    print (np.max(track_quarantined), "were in quarantine at the peak")

    return track_infected, track_new_infected, track_recovered, track_susceptible, track_dead, track_tested, track_quarantined, Population
