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
