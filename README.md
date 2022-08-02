# cv19

Hosting of our COVID-19 modelling efforts and data

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

## Development

We welcome anyone to contribute to and improve the code.
This includes fixing bugs or known issues,
updating documentation, and adding features.

If making changes to the code,
be sure to fork the repository,
make your changes on a new branch,
and submit a pull request through GitHub.

The code generally adheres to the
[PEP 8](https://peps.python.org/pep-0008/) style standards.
We use [Pylint](https://pylint.pycqa.org/en/latest/)
and [Flake8](https://flake8.pycqa.org/en/latest/)
to enforce good practices and
reduce the potential for bugs to be introduced.
To check whether or not your code will pass the exact tests
that are automatically run, first install both packages:

```sh
pip install pylint==2.14.4
pip install flake8==4.0.1
pip install editorconfig-checker==2.4.0
```

Then, run the tests:

```sh
./test/linters/pylint.py
./test/linters/flake8.py
ec -verbose
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
