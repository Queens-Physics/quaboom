# A list of all the adjustable parameters for the simulation


#### SIMULATION PARAMETERS ####

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

#### PERSON PARAMETERS ####






