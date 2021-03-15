import numpy as np
import Person
import Population
import Interaction_Sites
import Policy

# will_go_to_site parameters (prob person will go somewhere each day) 
A_WILL_GO_PROB = .05
B_WILL_GO_PROB = .4
C_WILL_GO_PROB = .8

# Testing parameters
TESTING_RATE = .8 #rate at which people get positive tests (testing rate/infected person)

# Polciy variables
initial_mask_mandate, initial_lockdown_mandate, initial_testing = False, False, False
lockdown_trigger, lockdown_day_trigger = None, 1
mask_trigger, mask_day_trigger = None, 25
testing_trigger, testing_day_trigger = None, 5
def RunEpidemic(nPop, n0, nDays):
    # Initalize the policy class
    policy = Policy.Policy(initial_mask_mandate=initial_mask_mandate, initial_lockdown_mandate=initial_lockdown_mandate, 
                           mask_trigger=mask_trigger, mask_day_trigger=mask_day_trigger, 
                           lockdown_trigger=lockdown_trigger, lockdown_day_trigger=lockdown_day_trigger, testing_rate=TESTING_RATE,
                           testing_trigger=testing_trigger,testing_day_trigger=testing_day_trigger,initial_testing=initial_testing)
    
    old_mask_mandate, old_lockdown, old_testing = initial_mask_mandate, initial_lockdown_mandate, initial_testing
    
    # Initialize the population
    pop = Population.Population(nPop, n0, policy=policy)
    
    # Initalize the interaction sites
    inter_sites = Interaction_Sites.Interaction_Sites(pop_obj=pop)
    
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
    track_masks = np.zeros(nDays, dtype=int)
    track_lockdown = np.zeros(nDays, dtype=int)
    track_testing_wait_list = np.zeros(nDays, dtype=int) # counts the number of people waiting to get tests each day
    # Loop over the number of days
    for day in range(nDays):

        ############### TRACKING STUFF ###############
        
        #Count all the different states of people
        track_infected[day] = pop.count_infected()
        track_susceptible[day] = pop.count_susceptible()
        track_recovered[day] = pop.count_recovered()
        track_dead[day] = pop.count_dead()
        track_tested[day] = pop.count_tested()
        track_quarantined[day] = pop.count_quarantined()
        track_masks[day] = old_mask_mandate
        track_lockdown[day] = old_lockdown
        track_testing_wait_list[day] = pop.get_testing_wait_list()
        
        new_tests = 0
        
        #track the days someone has been infected?
        if day != 0:
            new_recovered = track_recovered[day] - track_recovered[day-1]
            new_dead = track_dead[day] - track_dead[day-1]
            track_new_infected[day] = track_infected[day] - track_infected[day-1] + new_recovered + new_dead
            new_tests = track_testing_wait_list[day]-track_testing_wait_list[day-1]
            
        ############### POLICY STUFF ###############
        mask_mandate = policy.update_mask_mandate(day=day)
        if mask_mandate != old_mask_mandate:
            print("Day: {}, Mask Mandate: {}".format(day, mask_mandate))
        old_mask_mandate = mask_mandate
        
        lockdown = policy.update_lockdown(day=day)
        if lockdown != old_lockdown:
            print("Day: {}, Lockdown: {}".format(day, lockdown))
        old_lockdown = lockdown
        
        testing_ON = policy.update_testing(day)   
        if testing_ON != old_testing: 
            print("Day: {}, Testing: {}".format(day, testing_ON))
        old_testing = testing_ON
        
        ############### INTERACTION SITES STUFF ###############
        will_visit_A = inter_sites.will_visit_site(inter_sites.get_grade_A_sites(), A_WILL_GO_PROB)
        inter_sites.site_interaction(will_visit_A, day)
        if not lockdown:
            will_visit_B = inter_sites.will_visit_site(inter_sites.get_grade_B_sites(), B_WILL_GO_PROB)
            inter_sites.site_interaction(will_visit_B, day)
            will_visit_C = inter_sites.will_visit_site(inter_sites.get_grade_C_sites(), C_WILL_GO_PROB)
            inter_sites.site_interaction(will_visit_C, day)
        
        # Manage at home interactions
        inter_sites.house_interact(day)
        
        # Manage testing sites        
        if (testing_ON == True): 
            tests = policy.get_num_tests(new_tests)
            inter_sites.testing_site(tests,day)
        
        # Manage Quarantine
        pop.update_quarantine(day)
        
        ############### UPDATE POPULATION ###############
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

        print("Day: {}, infected: {}, recovered: {}, suceptible: {}, dead: {}, tested: {} total quarantined: {}".format(day, 
                                                                                      track_infected[day],
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
    
    return track_infected, track_new_infected, track_recovered, track_susceptible, track_dead, track_tested, track_quarantined, track_masks, track_lockdown, Population
