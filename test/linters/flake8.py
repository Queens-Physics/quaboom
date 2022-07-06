#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

from cv19 import CV19ROOT


def run_flake8():
    '''
    Run the Flake8 test on the module and some other files in the repository.
    Automatically ran on every pull request via GitHub actions.
    '''
    # Maximum line length.
    max_line_len = 300

    # Messages/warnings/errors to enable and disable.
    messages_disable = ["W503", "E741"]

    # List of files or directories to run the linter on.
    # Currently assumes that the working directory is where to get the files.
    file_list = ['cv19']
    file_list += [str(f) for f in Path(CV19ROOT).glob('test/**/*.py')]

    print("Running on:")
    for f in file_list:
        print(f"\t{f}")
    print("")

    # Overall command to run.
    cmd_list = ["flake8",
                "--jobs=1",
                f"--max-line-length={max_line_len}",
                f"--ignore={','.join(messages_disable)}"]

    # Unnamed arguments (the files to process).
    cmd_list += file_list

    # Run the flake8 command.
    # Return non-zero exit code upon failure.
    try:
        subprocess.run(cmd_list, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"\nflake8 returned with non-zero exit code: {e.returncode}.")
        return e.returncode

    return 0


if __name__ == "__main__":
    sys.exit(run_flake8())
