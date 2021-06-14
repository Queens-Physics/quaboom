#!/usr/bin/env python3

import sys
import subprocess

def run_pylint():
    # Messages/warnings/errors to enable and disable.
    messages_enable = ['all']
    messages_disable = ['R',
                        'line-too-long',
                        'missing-function-docstring',
                        'missing-class-docstring',
                        'missing-module-docstring',
                        'invalid-name',
                        'attribute-defined-outside-init',
                        'access-member-before-definition',
                        'fixme']

    # List of files or directories to run the linter on.
    file_list = ['Interaction_Sites.py', 'Person.py', 'Policy.py',
                 'Population.py', 'simulation.py',
                 'test_Person.py', 'test_Population.py',
                 'test/linters/pylint.py']

    # List of class names for which member attributes should not be checked (from pylint).
    ignored_classes = ['Interaction_Sites', 'Person', 'Policy',
                       'Population', 'simulation']

    # Overall command to run.
    cmd_list = ['python3', '-m', 'pylint',
                '--jobs=1',
                '--score=n',
                '--output-format=colorized',
                '--enable={0}'.format(','.join(messages_enable)),
                '--disable={0}'.format(','.join(messages_disable)),
                '--ignored-classes={0}'.format(','.join(ignored_classes))]

    # Unnamed arguments (the files to process).
    cmd_list += file_list

    # Run the pylint command.
    # Return non-zero exit code upon failure.
    try:
        t = subprocess.check_output(cmd_list, text=True)
        print(t)

    except subprocess.CalledProcessError as e:
        print(e.output)
        return e.returncode

    return 0

if __name__ == "__main__":
    sys.exit(run_pylint())
