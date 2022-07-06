import json
import multiprocessing
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as st
from matplotlib import pyplot as plt

from .simulation import simulation


def async_simulation(config_file, config_dir="", verbose=False):
    '''Does a single run of the simulation with the supplied configuration details.

    Parameters
    ----------
    config_file : str
        Filename for the configuration file.
    verbose : bool, default False
        Whether to output information from each day of the simulation.

    Returns
    -------
    tuple
        Arrays from the simulation.
    '''

    sim = simulation(config_file, config_dir=config_dir, verbose=verbose)
    sim.run()
    return sim.get_arrays()


def run_async(num_runs, config_file, save_name=None, num_cores=-1, config_dir="", verbose=False):
    '''Runs multiple simulations in parallel using the supplied configuration settings.

    Parameters
    ----------
    num_runs : int
        Number of times to run the simulation.
    config_file : str
        File containing the configuration details.
    save_name : str, default='simulation.pkl'
        Filename to save the simulation results upon completion.
    num_cores : int, default=-1
        Number of CPU cores to use when running the simulation. If -1, then use
        all available cores.
    verbose : bool, default False
        Whether to output information from each day of the simulation.

    Returns
    -------
    pandas.DataFrame
        Containing the results of the simulation in tabular format.
    '''

    if num_cores == -1:
        num_cores = multiprocessing.cpu_count()

    # Run all of the simulations
    multiprocessing.freeze_support()
    with multiprocessing.Pool(processes=num_cores) as pool:
        results = pool.starmap(async_simulation, ((config_file, config_dir, verbose) for _ in range(num_runs)))

    df = pd.DataFrame(results)
    if save_name is not None:
        with open(save_name, 'wb') as f:
            pickle.dump(df, f)

    return df


def _config_editor(config, param_name, value):
    '''Takes string form of a parameter's name (eg. policy_data.testing_rate)
    and changes it to the supplied value.

    Parameters
    ----------
    config : dict
        Dictionary containing the configuration settings.
    param_name : str
        String form of a parameter's name (eg. policy_data.testing_rate).
    value : object
        Value to set the parameter to.

    Raises
    ------
    ValueError
        If param_name is not in the config dictionary.
    '''

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
    '''Automatically measures the impact of various public health measures on different metrics.

    Parameters
    ----------
    base_config_file : str
        Filename for the configuration file to be used as a base.
    independent : dict
        A dictionary where the keys are names of the parameters that
        are independent variables, and the value is a list with all of the
        values that variable should take on (eg. to set the policy_data ->
        testing_rate to 0.1, 0.2, ..., 1, you would use the following dictionary:
            {"policy_data.testing_rate":[0.1*(x+1) for x in range(10)]})
        ** Currently only supports changing one independent variable **
    dependent : dict
        A dictionary where the keys are the names of the dependent
        variables, and the values are functions that take the simulation
        results as input and calculate the dependent variable.
        (eg. to measure total deaths and peak cases, use the following
        dictionary:
            {
                "total deaths":total_death_func,
                "peak cases":peak_case_func
            })
    num_runs : int, default = 8
        Number of times to run the simulation per configuration.
    num_cores : int, default=-1
        Number of CPU cores to use when running the simulation. If -1, then use
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
        Whether to output information from each day of the simulation.

    Returns
    -------
    pd.DataFrame
        Contains the values of the dependent variables
        for each of the supplied independent variable values.

    Raises
    ------
    NotImplementedError
        If the number of independent variables is not 1.
    '''

    if len(independent) > 1:
        raise NotImplementedError("Number of independent variables must be 1.")

    # Check if the length of the (only) independent variable is the same as the length
    # of the save_name list.
    if isinstance(save_name, (list, tuple)) and len(save_name) != len(list(independent.values())[0]):
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
        with open(base_config_file, encoding='utf-8') as f:
            temp_config = json.load(f)

        config_dir = Path(base_config_file).parent

        # Setting the parameters from the independent variables
        for key, value in zip(indep_keys, values):
            _config_editor(temp_config, key, value)

        # Run the simulations: returns an DataFrame
        scenario_save_name = None
        if isinstance(save_name, list):
            scenario_save_name = save_name[i]
        elif isinstance(save_name, str):
            scenario_save_name = save_name + f"{i:02}"
        data = run_async(num_runs, temp_config, num_cores=num_cores,
                         save_name=scenario_save_name, config_dir=config_dir, verbose=verbose)

        # Processing the results to get the dependent measurements, add to results
        result = [f(data) for f in dep_funcs]
        results.append(result)

    # Convert results to a dataframe
    results = pd.DataFrame(results, index=list(independent.values())[0], columns=dependent.keys())

    # Handle the case of multiple return values from the functions.
    # Checks that each function returns a value of the same length.
    # If single return value, just return the dataframe.
    if results.applymap(lambda x: isinstance(x, (float, int))).all(axis=None):
        return results
    # If multiple return values, return a tuple of dataframes.
    elif results.applymap(lambda x: isinstance(x, (tuple, list))).all(axis=None):
        resultslen = results.applymap(len)
        tuplelen = resultslen.iloc[0, 0]

        if (resultslen == tuplelen).all(axis=None):
            results_tuple = tuple(results.applymap(lambda x, index=j: x[index])
                                  for j in range(tuplelen))
            return results_tuple
        else:
            raise ValueError("Length of each element in DataFrame is not consistent.")
    else:
        raise ValueError("Type of each element in DataFrame is not consistent.")

    return results


def confidence_interval(config, parameterstoplot, num_runs=8, confidence=0.80, num_cores=-1, save_name=None, verbose=False):
    '''Plots the results of multiple simulations with confidence bands
    to give a better understanding of the trend of a given scenario.
    Displays a plot of the results.

    Parameters
    ----------
    config : str
        Filename of the configuration file to use for this simulation.
    parameters_to_plot : list
        List of parameters to include when plotting with the condifence interval.
    num_runs : int, default=8
        Number of times to run the simulation.
    confidence : float
        Confidence of the confidence bands, ie. the proportion of results
        that fall within the confidence bands. The range of this parameter
        should be (0, 1].
    num_cores : int, default=-1
        Number of cores to use when running the simulation. If -1, then use
        all available cores.
    save_name: str or None, default None
        Name to save the results under. Default None, which means don't save
        the results.
    verbose : bool, default False
        Whether to output information from each day of the simulation.
    '''

    result = run_async(num_runs, config, num_cores=num_cores, save_name=save_name, verbose=verbose)

    fig_ci, ax_ci = plt.subplots()
    z_score = st.norm.ppf(confidence)

    for col in result.columns:

        # If the column is of dtype boolean, then this analysis does
        # not apply
        if col not in parameterstoplot:
            continue

        # Analyze the results
        array = np.stack(
            result[col].to_numpy()
        )
        mean = array.mean(axis=0)
        std = array.std(axis=0)

        # Plotting mean and confidence bands
        ax_ci.plot(
            mean,
            label=col
        )
        ax_ci.fill_between(
            range(len(mean)),
            mean - z_score * std,
            mean + z_score * std,
            alpha=0.2
        )

    ax_ci.legend()
    fig_ci.show()


def confidence_interval_complex(*scenarios, z=2):
    '''Draws a plot that tracks one or more metrics in the simulation. The
    simulation is run many times to get a more accurate representation of
    the trends. The metric(s) is(are) drawn with confidence intervals.

    *Scenarios: one or more dictionaries that contain:
        - 'name': name of the scenario
        - 'params': parameters
        - 'metric': metric to plot
    z: the number of standard deviations above or below the mean to use for
        the confidence bands. For example,
        - z=1 => 66% confidence,
        - z=2 => 95% confidence,
        - z=3 => 99% confidence.

    This function draws a plot of the metrics over time.
    '''

    del z
    del scenarios

    code = '''
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
    '''

    raise NotImplementedError(("Function not yet implemented. "
                               "Current code:\n") + code)

# Metric calculator functions


def peak(data):
    '''Calculates the number of people infected at the peak, averaged over the
    simulations that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    tuple of float
        Number of people infected at the peak, averaged over the simulations that
        were run, and uncertainty.
    '''

    peak_infections = data['infected'].apply(max)
    return (peak_infections.mean(),
            peak_infections.std() / np.sqrt(len(peak_infections)))


def peak_date(data):
    '''Calculates the date of the peak, averaged over the simulations that were
    run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    tuple of float
        Date of the peak, averaged over the simulations that were run, and uncertainty.
    '''

    peak_infections_dates = data['infected'].apply(np.argmax)
    return (peak_infections_dates.mean(),
            peak_infections_dates.std() / np.sqrt(len(peak_infections_dates)))


def hospitalizations(data):
    '''Calculates the number of hospitalizations at the peak, averaged over the
    simulations that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    tuple of float
        Number of hospitalizations at the peak, averaged over the simulations that
        were run, and uncertainty.
    '''

    peak_hospitalizations = data['hospitalized'].apply(max)
    return (peak_hospitalizations.mean(),
            peak_hospitalizations.std() / np.sqrt(len(peak_hospitalizations)))


def deaths(data):
    '''The average number of total deaths over all simulations that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.
    Returns
    -------
    tuple of float
        Average number of total deaths over all simulations that were run
        and uncertainty.
    '''

    total_deaths = data['dead'].apply(max)
    return (total_deaths.mean(),
            total_deaths.std() / np.sqrt(len(total_deaths)))


def peak_quarantine(data):
    '''The number of people in quarantine at the peak, averaged over the simulations
    that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    tuple of float
        Number of people in quarantine at the peak, averaged over the simulations
        that were run, and uncertainty.
    '''

    peak_quarantined = data['quarantined'].apply(max)
    return (peak_quarantined.mean(),
            peak_quarantined.std() / np.sqrt(len(peak_quarantined)))


def peak_ICU(data):
    '''The number of people in ICU at the peak, averaged over the simulations
    that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    tuple of float
        Number of people in ICU at the peak, averaged over the simulations
        that were run, and uncertainty.
    '''

    peak_ICUs = data['ICU'].apply(max)
    return (peak_ICUs.mean(),
            peak_ICUs.std() / np.sqrt(len(peak_ICUs)))


def peak_deaths(data):
    '''The number of deaths at the peak, averaged over the simulations
    that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    tuple of float
        Number of deaths at the peak, averaged over the simulations
        that were run, and uncertainty.
    '''

    peak_death = data['dead'].apply(max)
    return (peak_death.mean(),
            peak_death.std() / np.sqrt(len(peak_death)))


def peak_hospitalization(data):
    '''The number of people in the hospital at the peak, averaged over the
    simulations that were run.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    tuple of float
        Number of people in the hospital at the peak, averaged over the simulations
        that were run, and uncertainty.
    '''

    peak_hospitalized = data['hospitalized'].apply(max)
    return (peak_hospitalized.mean(),
            peak_hospitalized.std() / np.sqrt(len(peak_hospitalized)))


def time_elapsed(data):
    '''Time elapsed for the simulation.

    Parameters
    ----------
    data : pandas.DataFrame
        Output from running a simulation.

    Returns
    -------
    tuple of float
        Average elapsed time of the simulations and uncertainty.
    '''

    simulation_times = data['time_elapsed'].apply(max)
    return (simulation_times.mean(),
            simulation_times.std() / np.sqrt(len(simulation_times)))


# Sample usage
if __name__ == "__main__":

    # Tabular mode
    table = tabular_mode(
        'config_files/main.json',
        {
            "population_data.prob_has_mask": [0.25, 0.50, 0.75, 1.00]
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
    parameters_to_plot = ["infected",
                          "new_infected",
                          "recovered",
                          "susceptible",
                          "dead",
                          "quarantined",
                          "inf_students",
                          "total_tested",
                          "new_tested",
                          "hospitalized",
                          "ICU",
                          "testing_enforced",
                          "masks_enforced",
                          "lockdown_enforced",
                          "time_elapsed"]

    confidence_interval('config_files/main.json', parameterstoplot=parameters_to_plot, confidence=0.9)

    input()
