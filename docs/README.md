# Documentation

## Setup

To ensure that all dependencies are installed, run the following:

```bash
pip install -r requirements.txt
```

This will install the required dependencies to run the code and
build the documentation. In particular for the documentation, the
packages `sphinx` and `sphinx-rtd-theme` must be available.

If developing and running code, you must set up the environment.
To do this, run the following in the repository:

```bash
./configure
source ./env.sh
```

This will ensure that sphinx can find the relevant code.
See the top-level folder README.md for additional details on
setting up the environment.

## Building the documentation

When in the `docs/` folder, simply run `make html` to build the documentation.
This will output the relevant pages into `docs/_build/html`. Run `make`
(with no arguments) to see other available options.

To remove all build files and clean up the documentation, run `make clean`.

## Contributing to the documentation

The documentation can be directly edited in some cases by editing the
relevant .rst files in the `docs/` folder. However, most of the time one
will want to edit the docstrings in the code, as those are automatically
formatted by sphinx. We use the numpy style for docstrings. See
[here](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html)
for information on how to structure docstrings, and
[here](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy)
for an example which uses the numpy formatting.
