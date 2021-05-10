import multiprocessing
from simulation import RunEpidemic
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import pickle

COLS = ["infected", "new_infected", "recovered", "susceptible", "dead", "hospitalized", "tested", "quarantined", "mask", "lockdown"]

PARAMS = {'nPop':10000, 'n0': 10, 'nDays':40}

def async_RunEpidemic(q, *args):
    results = RunEpidemic(*args)
    q.put(results[:-1])

def run_async(num_runs, *args, save_name='simulation.pkl'):

    # Make the queue and the parameters
    q = multiprocessing.Manager().Queue()

    # Run all of the simulations
    multiprocessing.freeze_support()
    with multiprocessing.Pool() as pool:
        pool.starmap(async_RunEpidemic, ((q, *args) for _ in range(num_runs)))

    # Grab and return all the loggers
    outputs = []
    while not q.empty():
        outputs.append(q.get())
    
    #TODO: It would be beneficial to make the output from the RunEpidemic function
    # a dictionary, so that if the order was changed it would not screw up
    # this output.
    df = pd.DataFrame(outputs, columns=COLS)
    with open(save_name, 'wb') as f:
         pickle.dump(df, f)

    return df

def order_sims(params, independent, dependent):
    '''Automatically measures the impact of various public health measures on different metrics.
    
    params: the parameters for the simulations
    independent: a dictionary where the keys are names of the parameters that
        are independent variables, and the value is a list with all of the
        values that variable should take on
        ** Currently only supports changing one independent variable **
    dependent: a dictionary where the keys are the names of the dependent
        variables, and the values are functions that take the simulation
        results as input and calculate the dependent variable
    
    returns a DataFrame that contains the values of the dependent variables 
        for each of the supplied independent variable values.
    '''
    
    if len(independent) > 1:
        raise NotImplementedError("Number of independent variables must be 1.")
    
    indep_keys = independent.keys()
    indep_vals = independent.values()
    dep_funcs = dependent.values() 
    
    # Mesh is list that contains the values of the independent parameters.
    # It guarantees that each combination of parameters will be run.
    mesh = [a.flatten() for a in np.meshgrid(*indep_vals)]

    # Results stores the results of the different scenarios
    results = []

    # Running through each scenario
    for values in zip(*mesh):

        # Setting the parameters from the independent variables
        for key, value in zip(indep_keys, values):
            params[key] = value
        
        # Run the simulations: returns an DataFrame
        #TODO: Make the simulation accept a parameters file
        data = run_async(8, params['nPop'], params['n0'], params['nDays'])

        # Processing the results to get the dependent measurements, add to results       
        result = list(map(lambda f: f(data), dep_funcs))
        results.append(result)

    # Convert results to a dataframe
    results = pd.DataFrame(results, index=list(independent.values())[0], columns=dependent.keys())

    return results

def confidence_interval(*scenarios, z=2):
    """Draws a plot that tracks one or more metrics in the simulation. The
    simulation is run many times to get a more accurate representation of
    the trends. The metric(s) is(are) drawn with confidence intervals.

    *scenarios: one or more dictionaries that contain:
        - 'name': name of the scenario
        - 'params': parameters
        - 'metric': metric to plot
    z: the number of standard deviations above or below the mean to use for
        the confidence bands. For example,
        - z=1 => 66% confidence, 
        - z=2 => 95% confidence,
        - z=3 => 99% confidence.
    
    This function draws a plot of the metrics over time.
    """

    fig, ax = plt.subplots()

    for scenario in scenarios:

        # Run the simulations for this scenario
        params = scenario['params']
        result = run_async(8, params['nPop'], params['n0'], params['nDays'], save_name=scenario['name'])

        # Analyze the results
        array = np.stack(
            result[scenario['metric']].to_numpy()
        )
        mean = array.mean(axis=0)
        std = array.std(axis=0)

        # Plotting mean and confidence bands
        ax.plot(
            mean, 
            label=scenario['name']
        )
        ax.fill_between(
            range(len(mean)),
            mean - z * std,
            mean + z * std,
            alpha=0.2
        )
    
    ax.legend()
    fig.show()


#### Metric calculator functions ####
def peak(data):
    infections = data['infected']
    return infections.apply(max).mean()

def peak_date(data):
    infections = data['infected']
    return infections.apply(np.argmax).mean()

def hospitalizations(data):
    return data['hospitalized'].apply(max).mean()

def deaths(data):
    return data['dead'].apply(max).mean()



# Sample usage
if __name__ == "__main__":

    # Tabular mode
    table = order_sims(
        {'nPop':10000, 'nDays':40}, 
        {"n0": [50, 100, 200, 400]}, 
        {"peak": peak, "peak_date": peak_date, "hospitalizations": hospitalizations, "deaths": deaths}
    )
    with open('results.pkl', 'wb') as f:
        pickle.dump(table, f)

    # Print table
    print(table)
    # Plot results
    ax = table.plot(secondary_y=['peak_date'])
    ax.set_ylabel("Number of people")
    ax.right_ax.set_ylabel("Date of peak")
    ax.set_xlabel("Number of people initially infected")
    plt.show()

    # Confidence interval mode
    scenario1 = {'name': 'High n0', "params": {'n0': 100, 'nDays': 40, 'nPop': 10000}, 'metric': 'infected'}
    scenario2 = {'name': 'Low n0', "params": {'n0': 10, 'nDays': 40, 'nPop': 10000}, 'metric': 'infected'}
    confidence_interval(scenario1, scenario2)
    input()
