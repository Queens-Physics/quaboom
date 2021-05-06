import multiprocessing
from simulation import RunEpidemic
import numpy as np
import pandas as pd

COLS = ["infected", "new_infected", "recovered", "susceptible", "dead", "hospitalized", "tested", "quarantined", "mask", "lockdown"]

def async_RunEpidemic(q, *args):
    results = RunEpidemic(*args)
    q.put(results[:-1])

def run_async(num_runs, *args):

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
    
    return pd.DataFrame(outputs, columns=COLS)

def order_sims(params, independent, dependent):
    '''Automatically measures the impact of various public health measures on different metrics.'''
    
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
        data = run_async(8, params['nPop'], params['n0'], params['nDays'])

        # Processing the results to get the dependent measurements, add to results       
        result = list(map(lambda f: f(data), dep_funcs))
        results.append(result)

    # Convert results to a dataframe
    results = pd.DataFrame(results, index=list(independent.values())[0], columns=dependent.keys())

    return results

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
    

import pickle

if __name__ == "__main__":
    
    x = order_sims({'nPop':10000, 'nDays':40}, {"n0": [10, 50, 100, 200, 500, 1000]}, {"peak": peak, "peak_date": peak_date, "hospitalizations": hospitalizations, "deaths": deaths})

    with open('results.pkl', 'wb') as f:
        pickle.dump(x, f)
    
    print(x)