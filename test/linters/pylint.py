#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

from cv19 import CV19ROOT


def run_pylint():
    """
    Run the Pylint test on the module and some other files in the repository.
    Automatically ran on every pull request via GitHub actions.
    """
    # Messages/warnings/errors to enable and disable.
    messages_enable = ['all']
    messages_disable = ['R',
                        'line-too-long',
                        'missing-module-docstring',
                        'invalid-name',
                        'attribute-defined-outside-init',
                        'access-member-before-definition',
                        'fixme']

    # List of files or directories to run the linter on.
    # Currently assumes that the working directory is where to get the files.
    file_list = ['cv19']
    file_list += [str(f) for f in Path(CV19ROOT).glob('test/**/*.py')]

    print("Running on:")
    for f in file_list:
        print(f"\t{f}")
    print("")

    # List of class names for which member attributes should not be checked (from pylint).
    ignored_classes = ['InteractionSites', 'Person', 'Policy',
                       'Population', 'Simulation']

    # Overall command to run.
    cmd_list = ["pylint",
                "--jobs=1",
                "--score=n",
                "--output-format=colorized",
                f"--enable={','.join(messages_enable)}",
                f"--disable={','.join(messages_disable)}",
                f"--ignored-classes={','.join(ignored_classes)}"]

    # Unnamed arguments (the files to process).
    cmd_list += file_list

    # Run the pylint command.
    # Return non-zero exit code upon failure.
    try:
        subprocess.run(cmd_list, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"\npylint returned with non-zero exit code: {e.returncode}.")
        return e.returncode

    return 0


if __name__ == "__main__":
    sys.exit(run_pylint())
