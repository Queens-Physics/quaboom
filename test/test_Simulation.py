#!/usr/bin/env python3

import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from cv19.simulation import Simulation


class TestSimulation(unittest.TestCase):
    """ Class used to test how the simulation actually runs..

    This code is run for each new pull request within the CV19 repository.

    Note
    ----
    This class holds code to check that the outputs of a run simulation are as expected. This differs from
    other unit test files, which focus on checking specific functions outside the context of a full
    simulation.
    """

    def setUp(self):
        """ Set up method for testing simulation runs.

        This function is called every time the class is initalized, and creates multiple
        simulation objects used for testing.
        """
        quarantine_config_file_1 = str(Path(Path(__file__).parent, "testing_config_files/main_quarantine_1.toml").resolve())
        self.quarantine_obj_1 = Simulation(quarantine_config_file_1, verbose=False)
        self.quarantine_obj_1.run()

        quarantine_config_file_2 = str(Path(Path(__file__).parent, "testing_config_files/main_quarantine_2.toml").resolve())
        self.quarantine_obj_2 = Simulation(quarantine_config_file_2, verbose=False)
        self.quarantine_obj_2.run()

    def tearDown(self):
        """ Tear down method for testing simulation runs.

        Currently not used, this function is called after all unit tests have been run.
        """

    def test_quarantine_1(self):
        """ Method used to make sure the simulation associated with quarantine_1 behaved as expected.

        This simulation has lots of infections to begin and no infection spread.

        Checks that there are no quarantines at the end of the simulation, and that no new quarantines
        take place after infections have died out. Also checks that we do not start with quarantines.
        Checks that no new quarantines appear without testing happening that day.
        """

        raw_data = self.quarantine_obj_1.get_tracking_dataframe()

        # Make sure we start and end with no quarantined
        self.assertTrue(raw_data['quarantined'].iloc[-1] == 0)
        self.assertTrue(raw_data['quarantined'].iloc[0] == 0)

        # Check that number of number of new tests is greater than or equal to
        # the number of new quarantines for a given day
        self.assertTrue((raw_data["new_tested"] >= raw_data["new_quarantined"]).all())

    def test_quarantine_2(self):
        """ Method used to make sure the simulation associated with quarantine_2 behaved as expected.

        This simulation focuses on making sure that uninfected, symptomatic tests (cold tests) behave as expected.
        It has no infections, but a very high cold probability.

        Currently, quarantine should only take place after a positive test. Therefore, we should see no quarantine
        in this simulaiton. Also will check that the number of interactions remains roughly consistent.
        """

        raw_data = self.quarantine_obj_2.get_tracking_dataframe()

        # Make sure there are tests and no one gets quarantined
        self.assertTrue(raw_data['new_tested'].gt(0).any() and raw_data['quarantined'].eq(0).all())

        n_interactions = raw_data['n_interactions_B']
        start_interactions_mean = n_interactions.iloc[:10].mean()
        end_interactions_mean = n_interactions.iloc[-10:].mean()

        # Make sure it falls within a standard deviation
        self.assertTrue(np.abs(start_interactions_mean - end_interactions_mean) < n_interactions.std())


if __name__ == '__main__':
    unittest.main()
