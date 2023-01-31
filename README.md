# cv19

Hosting of our COVID-19 modelling efforts and data

## Setup

### Python environment configuration

To run the code, ensure that you have a recent version of Python 3 installed.
The code has only been tested on Python 3.8 and 3.9.

If running locally, it is recommended to create a virtual environment.
To create a virtual environment called `env`, run the following:

```bash
python3 -m venv env
source env/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade setuptools wheel
```

Note that the name `env` is arbitrary.
After completing this step, the virtual environment will be created,
and you will only need to source the `activate` file each time
you open a new terminal instance
to switch back into it (`source env/bin/activate`).

To ensure that all dependencies are installed, run the following
(potentially in a virtual environment if you have set it up that way):

```bash
pip install -r requirements.txt
```

This will install the required dependencies to run the code and
build the documentation.

If you want to use Jupyter Notebooks, you will also need to install
the Jupyter Notebook and/or JupyterLab package(s)
depending on your preference.
Again, these can be installed in the virtual environment.

### Repository configuration

If running (or developing, testing, ...) the code,
you must also modify the environment for the repository itself.
To do this, run the following in top level directory:

```bash
./configure
source ./env.sh
```

The first line will generate the environment file,
while the second line will source it.
This ensures that the repository is in the `PYTHONPATH` variable.
It also sets the `CV19ROOT` environment variable,
which is used in several parts of the code
so that the absolute location of the repository is known.
Once the repository has been cloned and configured,
the `configure` script does not need to be run again.

### After configuration

When your Python environment and the repository are configured,
you will only need to source the environment files when coming back to the code.
Simply change into the path of the repository and run:

```bash
source env/bin/activate  # if using a virtual environment
source env.sh  # always required
```

For Jupyter Notebooks, the following is needed in the first cell
to source the environment after the `configure` script has been run:

```python
import sys
from dotenv import load_dotenv, dotenv_values
load_dotenv("../cv19.env")
sys.path.append(dotenv_values("../cv19.env")["CV19ROOT"])
```

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
pip install pylint==2.15.10
pip install flake8==5.0.4
pip install flake8-quotes==3.3.2
pip install editorconfig-checker==2.7.1
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
