# Description of simulation framework:

Queen’s University Agent-Based Outbreak Outcome Model (QUABOOM) is an agent-based, object-oriented Monte Carlo simulation framework for modeling epidemics for a range of population sizes. The parameters of the simulation are easily modifiable by the user, allowing for comparison to real-life outbreaks and public health policies. The simulation framework gives users the ability to study case severity, masking, vaccination, testing, epidemic parameters (such as herd immunity, reproductive number), multiple disease variants, and the effect of a student population on disease spread.

This simulation framework was used to propose a targeted capacity restriction approach in this paper: < link to paper > 

The simulation code is written in python, so it can be run through any Python interpreter. To run the simulation, clone your fork of the repository to your local machine, and follow the **Setup** instructions listed below to make sure you have all the necessary dependencies and set up the environment correctly. 

## Setup

To ensure that all dependencies are installed, run the following:

```bash
pip install -r requirements.txt
```

This will install the required dependencies to run the code and
build the documentation. Note that you may (and probably should)
need to run the above command with the `--user` flag.

If developing and running code, you must set up the environment.
To do this, run the following in the repository:

```bash
./configure
source ./env.sh
```

The first line will generate the environment,
while the second line will source it.
This ensures that the repository is in the `PYTHONPATH` environment variable.
It also sets the `CV19ROOT` environment variable, which is used
in several parts of the code so that the absolute location of
the repository is known.

For Jupyter notebooks, one needs to add the following to the first cell:

```python
import sys
from dotenv import load_dotenv, dotenv_values
load_dotenv("../cv19.env")
sys.path.append(dotenv_values("../cv19.env")["CV19ROOT"])
```
## How to use simulation framework

To modify simulation parameters, navigate to ```bash cv19/config_files/``` and open main.toml or disease.toml to edit general or disease-related parameters. To learn more about how the simulation works, navigate to ```bash cv19/cv19/```, where all of the classes that are used in the simulation are stored. The ```bash cv19/data/``` directory holds the real-life statistics that the simulation parameters are based on. The  ```bash cv19/notebooks/``` directory has two notebooks that show examples of how to use the simulation framework. Using ```bash cv19/notebooks/run_epidemic_plot.ipynb```, you can run the simulation once and see the outcome of the epidemic outbreak graphically. There is a second notebook in that directory, ```bash cv19/notebooks/parallel.ipynb```, which allows you to run multiple simulations in parallel. Within that notebook, “confidence interval mode” allows you to observe the trend of a particular simulation setup averaged over a given number of runs. In that same notebook, “tabular mode” lets you study the effect of a simulation parameter (such as masking efficiency) on the number of infections (or deaths, or quarantined individuals). These notebooks showcase only a few of the many types of analysis that can be conducted with our simulation framework.

## Development

We welcome anyone to contribute to and improve the code.
This includes fixing bugs or known issues,
updating documentation, and adding features.

If making changes to the code,
be sure to fork the repository,
make your changes on a new branch,
and submit a pull request through GitHub.

The Python code generally adheres to the
[PEP 8](https://peps.python.org/pep-0008/) style standards.
We use [Pylint](https://pylint.pycqa.org/en/latest/)
and [Flake8](https://flake8.pycqa.org/en/latest/)
to enforce good practices and
reduce the potential for bugs to be introduced.
We also use an [EditorConfig](https://editorconfig.org/) linter
to enforce a consistent style across all files,
including configuration files and READMEs.
To check whether or not your code will pass the exact tests
that are automatically run, first install the necessary packages
(along with an extension for Flake8):

```sh
pip install pylint==2.14.4
pip install flake8==5.0.4
pip install flake8-quotes==3.3.1
pip install editorconfig-checker==2.4.0
```

Then, run the tests:

```sh
./test/linters/pylint.py
./test/linters/flake8.py
ec
```

Each file has certain parameters that are modified
or certain warnings that are disabled.

To automatically update your code to conform to PEP 8,
you can use the [autopep8](https://pypi.org/project/autopep8/) tool.
First, install autopep8:

```sh
pip install autopep8
```

Then, run autopep8, changing files in place:

```sh
autopep8 --in-place --ignore=E501 cv19/*.py
```

Note that it may not fix everything,
and some manual intervention may be required.
In particular, it is currently recommended to
fix line length problems manually,
either by moving comments around,
changing variable names,
or using continued indentation depending on the context.
Many Pylint warnings will also not be fixed automatically
by autopep8.
