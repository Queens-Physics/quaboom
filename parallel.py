import multiprocessing
from simulation import simulation
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import pickle
import scipy.stats as st
import json
import os

COLS = ["infected", "new_infected", "recovered", "susceptible", "dead",
        "quarantined", "inf_students", "total_tested", "new_tested", 
        "testing_enforced", "masks_enforced", "lockdown_enforced"]

def async_simulation(config_file, verbose=False):
    """Does a single run of the simulation with the supplied configuration details.

    Parameters
    ----------
    config_file : str
        filename for the configuration file
    verbose : bool, default False
        whether to output information from each day of the simulation
    
    Returns
    -------
    tuple
        arrays from the simulation

    """

    sim = simulation(config_file, verbose=verbose)
    sim.run()
    return sim.get_arrays()

def run_async(num_runs, config_file, save_name=None, num_cores=-1, verbose=False):
    """Runs multiple simulations in parallel using the supplied configuration settings.

    Parameters
    ----------
    num_runs : int
        number of times to run the simulation
    config_file : str
        file containing the configuration details
    save_name : str, default='simulation.pkl'
        filename to save the simulation results upon completion
    num_cores : int, default=-1
        number of CPU cores to use when running the simulation. If -1, then use
        all available cores.   
    verbose : bool, default False
        whether to output information from each day of the simulation
    
    Returns
    -------
    pandas.DataFrame
        containing the results of the simulation in tabular format
    """

    if num_cores == -1:
        num_cores = multiprocessing.cpu_count()

    # Run all of the simulations
    multiprocessing.freeze_support()
    with multiprocessing.Pool(processes=num_cores) as pool:
        results = pool.starmap(async_simulation, ((config_file, verbose) for _ in range(num_runs)))

    df = pd.DataFrame(results)
    if save_name != None:
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
            x[param] = value
        
        # Not the last parameter: advance in the dictionary
        else:
            x = x[param]



def tabular_mode(base_config_file, independent, dependent, num_runs=8, num_cores=8, save_name=None, verbose=False):
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
    num_cores : int, default=-1
        number of CPU cores to use when running the simulation. If -1, then use
        all available cores.
    save_name : str or list[str] or None, default None
        The filename(s) to use when saving results from the simulation. If using
        a string, the supplied string with act as the base filename with digits
        differentiating the scenarios (eg. if save_name == "simulation", then the
        saved files will have the form "simulation01.pkl", "simulation02.pkl", ...).
        If using a list, then the list must be exactly as long as the number of values
        for the independent variable, and each scenario will be saved under its 
        corresponding filename. If None, then don't save any results.
    verbose : bool, default False
        whether to output information from each day of the simulation

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
    
    # Check if the length of the (only) independent variable is the same as the length
    # of the save_name list.
    if type(save_name) is list and len(save_name) != len(list(independent.values())[0]):
        raise ValueError("'save_name' is a list and not the same length as the independent variable. Refer to the documentation for details.")

    indep_keys = independent.keys()
    indep_vals = independent.values()
    dep_funcs = dependent.values() 
    
    # Mesh is list that contains the values of the independent parameters.
    # It guarantees that each combination of parameters will be run.
    mesh = [a.flatten() for a in np.meshgrid(*indep_vals)]

    # Results stores the results of the different scenarios
    results = []

    # Running through each scenario
    for i, values in enumerate(zip(*mesh)):

        # Load the json file
        with open(base_config_file) as f:
            temp_config = json.load(f)

        # Setting the parameters from the independent variables
        for key, value in zip(indep_keys, values):
            _config_editor(temp_config, key, value)

        # Run the simulations: returns an DataFrame
        scenario_save_name = None
        if type(save_name) is list:
            scenario_save_name = save_name[i]
        elif type(save_name) is str:
            scenario_save_name = save_name + '{:02}'.format(i)
        data = run_async(num_runs, temp_config, num_cores=num_cores, 
                        save_name=scenario_save_name, verbose=verbose)

        # Processing the results to get the dependent measurements, add to results       
        result = [f(data) for f in dep_funcs]
        results.append(result)

    # Convert results to a dataframe
    results = pd.DataFrame(results, index=list(independent.values())[0], columns=dependent.keys())

    return results

def confidence_interval(config, num_runs=8, confidence=0.80, num_cores=-1, save_name=None, verbose=False):
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
    num_cores : int, default=-1
        number of cores to use when running the simulation. If -1, then use
        all available cores.
    save_name: str or None, default None
        name to save the results under. Default None, which means don't save
        the results.
    verbose : bool, default False
        whether to output information from each day of the simulation
    """

    result = run_async(num_runs, config, num_cores=num_cores, save_name=save_name, verbose=verbose)

    fig, ax = plt.subplots()
    z_score = st.norm.ppf(confidence)

    for col in result.columns:

        # If the column is of dtype boolean, then this analysis does
        # not apply
        if col in ["testing_enforced", "masks_enforced", "lockdown_enforced"]:
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
    """Calculates the number of people infected at the peak, averaged over the
    simulations that were run. 
    
    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    float
        number of people infected at the peak, averaged over the simulations that
        were run.
    """
    infections = data['infected']
    return infections.apply(max).mean()

def peak_date(data):
    """Calculates the date of the peak, averaged over the simulations that were
    run. 
    
    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    float
        date of the peak, averaged over the simulations that were run.
    """
    infections = data['infected']
    return infections.apply(np.argmax).mean()

def hospitalizations(data):
    """Calculates the number of hospitalizations at the peak, averaged over the
    simulations that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.
    
    Returns
    -------
    float
        number of hospitalizations at the peak, averaged over the simulations that
        were run.
    """

    return data['hospitalized'].apply(max).mean()

def deaths(data):
    """The average number of total deaths over all simulations that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.
    Returns
    -------
    float
        average number of total deaths over all simulation that were run.
    """

    return data['dead'].apply(max).mean()

def peak_quarantine(data):
    """The number of people in quarantine at the peak, averaged over the simulations
    that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    float
        number of people in quarantine at the peak, averaged over the simulations
        that were run.
    """
    return data['quarantined'].apply(max).mean()


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
            'peak quarantine': peak_quarantine, 
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

    input()


    
