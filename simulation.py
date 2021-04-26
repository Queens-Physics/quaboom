import numpy as np
import Person
import Population
import Interaction_Sites
import Policy

# will_go_to_site parameters (prob person will go somewhere each day) 
A_WILL_GO_PROB = .05
B_WILL_GO_PROB = .4
C_WILL_GO_PROB = .8
LECT_GO_PROB = .8
STUDY_GO_PROB = .2
FOOD_GO_PROB = .1

# Visitor parameters
N_VIS_OPTION = [0, 1, 2, 3]
N_VIS_PROB = [0.7, 0.17, 0.08, 0.05]
vis_age_lower = 16
vis_age_upper = 60
# those are both arbitrary

# Testing parameters
TESTING_RATE = 0.5 #rate at which people get positive tests (testing rate/infected person)
test_baseline = 100 #starting test number

# Polciy variables
initial_mask_mandate, initial_lockdown_mandate, initial_testing = False, False, False
lockdown_trigger, lockdown_day_trigger = None, 5
mask_trigger, mask_day_trigger = None, 5
testing_trigger, testing_day_trigger = None, 5
initial_students, students_day_trigger = False, 20 ## 20

def RunEpidemic(nPop, n0, nDays):
    # Initalize the policy class
    policy = Policy.Policy(initial_mask_mandate=initial_mask_mandate, initial_lockdown_mandate=initial_lockdown_mandate, 
                           mask_trigger=mask_trigger, mask_day_trigger=mask_day_trigger, 
                           lockdown_trigger=lockdown_trigger, lockdown_day_trigger=lockdown_day_trigger, testing_rate=TESTING_RATE,
                           testing_trigger=testing_trigger, testing_day_trigger=testing_day_trigger, initial_testing=initial_testing,
                           baseline_testing = test_baseline, students_mandate=initial_students, students_day_trigger=students_day_trigger)
    
    old_mask_mandate, old_lockdown, old_testing = initial_mask_mandate, initial_lockdown_mandate, initial_testing
    old_students = initial_students
    
    # Initialize the population
    pop = Population.Population(nPop, n0, policy=policy)
    
    # Initalize the interaction sites
    inter_sites = Interaction_Sites.Interaction_Sites(pop_obj=pop)
    
    # Link the pop and inter_sites to the policy class
    policy.set_simulation(population=pop, interaction_sites=inter_sites)
    
    # Arrays to store the values during the simulation                   
    track_new_infected = np.zeros(nDays, dtype=int)      # new infections 
    track_infected = np.zeros(nDays, dtype=int)          # currently infected 
    track_susceptible = np.zeros(nDays, dtype=int)       # never been exposed
    track_recovered = np.zeros(nDays, dtype=int)         # total recovered
    track_dead = np.zeros(nDays, dtype=int)              # total deaths
    track_hospitalized = np.zeros(nDays, dtype=int)      # total hospitalizations
    track_tested = np.zeros(nDays, dtype=int)            # total tested individuals
    track_quarantined = np.zeros(nDays, dtype=int)       # population currently in quarantine ACTUALLY DOES TOTAL QUARINTIED 
    track_masks = np.zeros(nDays, dtype=int)

    track_lockdown = np.zeros(nDays, dtype=int)
    track_testing_wait_list = np.zeros(nDays, dtype=int) # counts the number of people waiting to get tests each day
    track_inf_students = np.zeros(nDays, dtype=int) # counts number of students infected each day

    # Loop over the number of days
    for day in range(nDays):

        ############### TRACKING STUFF ###############
        
        #Count all the different states of people
        track_infected[day] = pop.count_infected()
        track_susceptible[day] = pop.count_susceptible()
        track_recovered[day] = pop.count_recovered()
        track_dead[day] = pop.count_dead()
        track_hospitalized[day] = pop.count_hospitalized()
        track_tested[day] = pop.count_tested()
        track_quarantined[day] = pop.count_quarantined()
        track_masks[day] = old_mask_mandate
        track_lockdown[day] = old_lockdown
        track_testing_wait_list[day] = pop.get_testing_wait_list()
        track_new_quarantined[day] = pop.get_new_quarantined()
        track_inf_students[day] = pop.count_infected_students()
        
        new_tests = 0
        
        #track the days someone has been infected?
        if day != 0:
            new_recovered = track_recovered[day] - track_recovered[day-1]
            new_dead = track_dead[day] - track_dead[day-1]
            track_new_infected[day] = track_infected[day] - track_infected[day-1] + new_recovered + new_dead
            track_new_tested[day] = track_tested[day] - track_tested[day-1]
                
            
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

        students_go = policy.check_students(day=day)
        if students_go != old_students:
            print("Day: {}, Uni Mandate: {}".format(day, students_go))
        old_students = students_go
        
        ############### VISITOR STUFF ###############
        #add a random number of visitors to the population
        num_vis = np.random.choice(a=N_VIS_OPTION, p=N_VIS_PROB)
        visitors_ind = [x for x in range(nPop, nPop+num_vis-1)]
        
        for i in range(0, num_vis):
            vis_age = np.random.randint(vis_age_lower,vis_age_upper)
            
            visitor = Person.Person(index=i+nPop, infected=True, recovered=False, dead=False, quarantined=False, 
                               quarantined_day=None, infected_day=None, recovered_day=None, death_day=None,
                               others_infected=None, cure_days=None, recent_infections=None, age=vis_age, job=None,
                               house_index=None, isolation_tendencies=0.2, case_severity='Mild', has_mask=True)
            pop.population.append(visitor)
        
        ############### INTERACTION SITES STUFF ###############
        will_visit_A = inter_sites.will_visit_site(inter_sites.get_grade_A_sites(), A_WILL_GO_PROB)
        inter_sites.site_interaction(will_visit_A, day)
        if not lockdown:
            will_visit_B = inter_sites.will_visit_site(inter_sites.get_grade_B_sites(), B_WILL_GO_PROB)
            inter_sites.site_interaction(will_visit_B, day)
            will_visit_C = inter_sites.will_visit_site(inter_sites.get_grade_C_sites(), C_WILL_GO_PROB)
            inter_sites.site_interaction(will_visit_C, day)
        if students_go:
            will_visit_study = inter_sites.will_visit_site(inter_sites.get_study_sites(), STUDY_GO_PROB)
            inter_sites.site_interaction(will_visit_study, day)
            will_visit_food = inter_sites.will_visit_site(inter_sites.get_food_sites(), FOOD_GO_PROB)
            inter_sites.site_interaction(will_visit_food, day)
            if not lockdown:
                will_visit_lects = inter_sites.will_visit_site(inter_sites.get_lect_sites(), LECT_GO_PROB)
                inter_sites.site_interaction(will_visit_lects, day)
        
        # Manage at home interactions
        inter_sites.house_interact(day)
        
        # Manage testing sites        
        if (testing_ON): 
            tests = policy.get_num_tests(track_testing_wait_list[day])
            inter_sites.testing_site(tests,day)

        
        # Manage Quarantine
        pop.update_quarantine(day)
        
        
        ############### UPDATE POPULATION ###############
        # remove the guest visitors
        pop.remove_visitors(visitors_ind)
        
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


        print("Day: {}, infected: {}, recovered: {}, suceptible: {}, dead: {}, hospitalized: {}, tested: {} total quarantined: {}".format(day, 
                                                                                      track_infected[day],
                                                                                      track_recovered[day],
                                                                                      track_susceptible[day],
                                                                                      track_dead[day], 
                                                                                      track_hospitalized[day],
                                                                                      track_tested[day],
                                                                                      track_quarantined[day],
                                                                                      track_inf_students[day]))
    print("At the end, ", track_susceptible[-1], "never got it")
    print(track_dead[-1], "died")
    print(np.max(track_infected), "had it at the peak")
    print(track_tested[day], "have been tested")
    print (np.max(track_quarantined), "were in quarantine at the peak")
    print(np.max(track_hospitalized), "at peak hospitalizations")
    print(np.max(track_dead[-1]), "at peak deaths")
    

    return track_infected, track_new_infected, track_recovered, track_susceptible, track_dead, track_hospitalized, track_tested, track_quarantined, track_masks, track_lockdown, Population

