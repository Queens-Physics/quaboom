import multiprocessing
from simulation import simulation
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import pickle
import scipy.stats as st
import json
import os

COLS = ["infected", "new_infected", "recovered", "susceptible", "dead", "hospitalized", "tested", "quarantined", "mask", "lockdown"]

def async_simulation(config_file):
    """Does a single run of the simulation with the supplied configuration details.

    Parameters
    ----------
    config_file : str
        filename for the configuration file
    
    Returns
    -------
    tuple
        arrays from the simulation

    """

    sim = simulation(config_file)
    sim.run()
    return sim.get_arrays()

def run_async(num_runs, config_file, save_name='simulation.pkl'):
    """Runs multiple simulations in parallel using the supplied configuration settings.

    Parameters
    ----------
    num_runs : int
        number of times to run the simulation
    config_file : str
        file containing the configuration details
    save_name : str, default='simulation.pkl'
        filename to save the simulation results upon completion
    
    Returns
    -------
    pandas.DataFrame
        containing the results of the simulation in tabular format
    """

    # Run all of the simulations
    multiprocessing.freeze_support()
    with multiprocessing.Pool() as pool:
        results = pool.map(async_simulation, (config_file for _ in range(num_runs)))

    #TODO: It would be beneficial to make the output from the RunEpidemic function
    # a dictionary, so that if the order was changed it would not screw up
    # this output.
    df = pd.DataFrame(results, columns=COLS)
    with open(save_name, 'wb') as f:
        pickle.dump(df, f)

    return df

def _config_editor(config, param_name, value):
    """Takes string form of a parameter's name (eg. policy_data.testing_rate) 
    and changes it to the supplied value.

    Parameters
    ----------
    config : dict
        dictionary containing the configuration settings
    param_name : str
        string form of a parameter's name (eg. policy_data.testing_rate)
    value : object
        value to set the parameter to

    Raises
    ------
    ValueError
        If param_name is not in the config dictionary
    """

    x = config
    param_names = param_name.split('.')
    for i, param in enumerate(param_names):
        if param not in x.keys():
            raise ValueError(f"The supplied param_name {param_name} is not in the configuration file")

        # Last parameter: set the value now
        if i == len(param_names) - 1:
            x[param] = int(value)
        
        # Not the last parameter: advance in the dictionary
        else:
            x = x[param]



def tabular_mode(base_config_file, independent, dependent, num_runs=8):
    """Automatically measures the impact of various public health measures on different metrics.
    
    Parameters
    ----------
    base_config_file : str
        filename for the configuration file to be used as a base
    independent : dict
        a dictionary where the keys are names of the parameters that
        are independent variables, and the value is a list with all of the
        values that variable should take on
        Eg. to set the policy_data -> testing_rate to 0.1, 0.2, ..., 1, you
        would use the following dictionary:
            {"policy_data.testing_rate":[0.1*(x+1) for x in range(10)]}
        ** Currently only supports changing one independent variable **
    dependent : dict
        a dictionary where the keys are the names of the dependent
        variables, and the values are functions that take the simulation
        results as input and calculate the dependent variable.
        Eg. to measure total deaths and peak cases, use the following
        dictionary:
            {
                "total deaths":total_death_func, 
                "peak cases":peak_case_func
            }
    num_runs : int, default = 8
        number of times to run the simulation per configuration

    
    Returns
    -------
    pd.DataFrame
        contains the values of the dependent variables 
        for each of the supplied independent variable values.

    Raises
    ------
    NotImplementedError
        if the number of independent variables is not 1
    """
    
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

        # Load the json file
        with open(base_config_file) as f:
            temp_config = json.load(f)

        # Setting the parameters from the independent variables
        for key, value in zip(indep_keys, values):
            _config_editor(temp_config, key, value)

        # Writing a temporary configuration file to give to the simulation
        temp_config_file = 'config_files/temp.json'
        with open(temp_config_file, 'w') as f:
            json.dump(temp_config, f)

        # Run the simulations: returns an DataFrame
        #TODO: Make the simulation accept a parameters file
        data = run_async(num_runs, temp_config_file)

        # Processing the results to get the dependent measurements, add to results       
        result = list(map(lambda f: f(data), dep_funcs))
        results.append(result)

    # Convert results to a dataframe
    results = pd.DataFrame(results, index=list(independent.values())[0], columns=dependent.keys())

    # Removing the temp json file
    os.remove('config_files/temp.json')

    return results

def confidence_interval(config, num_runs=8, confidence=0.80):
    """Plots the results of multiple simulations with confidence bands
    to give a better understanding of the trend of a given scenario.
    Displays a plot of the results.

    Parameters
    ----------
    config : str
        filename of the configuration file to use for this simulation
    num_runs : int, default=8
        number of times to run the simulation
    confidence : float
        confidence of the confidence bands, ie. the proportion of results
        that fall within the confidence bands. The range of this parameter 
        should be (0, 1].
    """

    result = run_async(num_runs, config)

    fig, ax = plt.subplots()
    z_score = st.norm.ppf(confidence)

    for col in result.columns:

        # If the column is of dtype boolean, then this analysis does
        # not apply
        if col in ['mask', 'lockdown']:
            continue

        # Analyze the results
        array = np.stack(
            result[col].to_numpy()
        )
        mean = array.mean(axis=0)
        std = array.std(axis=0)

        # Plotting mean and confidence bands
        ax.plot(
            mean, 
            label=col
        )
        ax.fill_between(
            range(len(mean)),
            mean - z_score * std,
            mean + z_score * std,
            alpha=0.2
        )
    
    ax.legend()
    fig.show()

def confidence_interval_complex(*scenarios, z=2):
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

    raise NotImplementedError()

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
    table = tabular_mode(
        'config_files/main.json', 
        {
            "population_data.prob_has_mask":[1/4, 1/2, 3/4, 1]
        }, 
        {
            'peak cases': peak, 
            'peak hospitalizations': hospitalizations, 
            'cumulative deaths': deaths
        }
    )
    print(table)
    # Plot results
    ax = table.plot()
    ax.set_xlabel("Proportion of people wearing masks")
    plt.show()

    # Confidence interval mode
    confidence_interval('config_files/main.json', confidence=0.9)


    
