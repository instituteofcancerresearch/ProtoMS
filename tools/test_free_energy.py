"""Execute with 'python2.7 test_free_energy.py'"""

import pymbar
import numpy as np
import unittest
from free_energy_base import BAR, MBAR, TI, get_arg_parser
from free_energy_base import CompositePMF, FreeEnergy, PMF, Result
from simulationobjects import boltz, SnapshotResults
import calc_dg2
import calc_ti_decomposed
import calc_dg_cycle


class TestBAR(unittest.TestCase):
    estimator_class = BAR

    def setUp(self):
        """Create a test based on the pymbar HarmonicOscillatorsTestCase.
        """
        self.test = pymbar.testsystems.HarmonicOscillatorsTestCase(
            O_k=[0, 0, 0, 0, 0],
            K_k=[4., 5., 6., 7., 8.])
        # k = sample state index
        # l = eval state index
        # n = sample index
        self.x_kn, self.u_kln, self.N_k = self.test.sample(N_k=[10E4]*5,
                                                           mode='u_kln')

        self.lambdas = np.linspace(0., 1., len(self.N_k))
        self.series = []
        for lam, state in zip(self.lambdas, self.u_kln):
            snapshot = SnapshotResults()
            snapshot.feenergies = {lam: state[i]
                                   for i, lam in enumerate(self.lambdas)}
            snapshot.lam = [lam]
            self.series.append(snapshot)

        self.estimator = self.estimator_class(list(self.lambdas))
        self.add_data()

    def add_data(self):
        for series in self.series:
            self.estimator.add_data(series)

    def test_free_energies(self):
        """Check that free energies returned by the estimator's calculate
        method match the analytical results for the system.
        """

        # default test parameters use thermodynamic beta = 1
        pmf = self.estimator.calculate(temp=1/boltz)
        for fe1, fe2 in zip(pmf.values, self.test.analytical_free_energies()):
            self.assertAlmostEqual(fe1, fe2, places=1)

    def test_getitem(self):
        lens = [series.shape[-1]
                for series in self.estimator.data]

        for dN in (10, 20, 50, 100, 500):
            new_est = self.estimator[dN:]
            sliced_lens = [series.shape[-1]
                           for series in new_est.data]

            for l1, l2 in zip(lens, sliced_lens):
                self.assertEqual(l1, l2 + dN)

        # check that new_est is a different instance
        self.assertIsNot(self.estimator, new_est)


class TestMBAR(TestBAR):
    estimator_class = MBAR


class TestTI(TestBAR):
    estimator_class = TI

    def add_data(self):
        """For the Harmonic oscillator it is simple to work out the gradient
        of the energy with respect to lambda under certain
        conditions. This data is spoofed into series.forwfe such that
        when the estimator calculates the gradient it recovers the
        correct values. Requires strictly linear scaling of spring
        constants, and for all potentials to have the same bond length!

        dU(\lambda)/d\lambda = (k_1-k_0)/2*(x-b_0)^2
        """
        dlam = 0.001
        for series, state in zip(self.series, self.u_kln):
            series.lamb = [series.lam[0]-dlam]
            series.lamf = [series.lam[0]+dlam]
            series.forwfe = dlam*2*(series.feenergies[1.0] -
                                    series.feenergies[0.0])
            series.backfe = np.zeros_like(series.forwfe)
            self.estimator.add_data(series)


class TestArgumentParsers(unittest.TestCase):
    """Check for errors in the inheritance scheme used for argument parsers"""
    def test_base_parser(self):
        get_arg_parser()

    def test_dg2_parser(self):
        calc_dg2.get_arg_parser()

    def test_ti_decomposed(self):
        calc_ti_decomposed.get_arg_parser()

    def test_dg_cycle(self):
        calc_dg_cycle.get_arg_parser()


class TestCompositePMF(unittest.TestCase):
    def setUp(self):
        self.pmf_values = np.linspace(0., 5., 16)
        lambdas = np.linspace(0., 1., 16)
        self.pmfs = [PMF(lambdas, list(self.pmf_values*i*0.05))
                     for i in xrange(1, 3)]

    def test_init(self):
        """Test that validation of data lambda values during construction
        works correctly. Must all be the same else a ValueError should be
        raised."""
        CompositePMF(self.pmfs[0])
        CompositePMF(*self.pmfs)
        self.pmfs[0].lambdas = np.linspace(0., 2., 16)
        with self.assertRaises(ValueError):
            CompositePMF(*self.pmfs)

    def test_dG(self):
        single = CompositePMF(self.pmfs[0])
        double = CompositePMF(*self.pmfs)
        self.assertEqual(single.dG, FreeEnergy(self.pmf_values[-1]*0.05, 0.))
        self.assertEqual(double.dG.value, self.pmf_values[-1]*0.05*1.5)

    def test_negation(self):
        """Test use of negation operator"""
        single_pmf = CompositePMF(self.pmfs[0])
        double_pmf = CompositePMF(*self.pmfs)

        # as copy operator has been used check that data of original
        # object is not changed by the copied version
        pre = single_pmf.dG
        -single_pmf
        self.assertEqual(pre, single_pmf.dG)

        # check for expected behaviours
        self.assertEqual((-single_pmf).dG, -(single_pmf.dG))
        self.assertEqual((-double_pmf).dG, -(double_pmf.dG))

    def test_addition(self):
        """Test addition"""
        single_pmf = CompositePMF(self.pmfs[0])
        double_pmf = CompositePMF(*self.pmfs)

        self.assertEqual((single_pmf+single_pmf).dG.value,
                         single_pmf.dG.value*2)
        self.assertEqual((double_pmf+single_pmf).dG.value,
                         single_pmf.dG.value*2.5)


class TestResult(unittest.TestCase):
    def setUp(self):
        self.pmf_values = np.linspace(0., 5., 16)
        lambdas = np.linspace(0., 1., 16)
        self.pmfs = [PMF(lambdas, list(self.pmf_values*i*0.05))
                     for i in xrange(1, 4)]
        self.pmfs2 = [PMF(lambdas, list(self.pmf_values*2*i*0.05))
                      for i in xrange(1, 4)]

    def test_init(self):
        """Test that validation of data lambda values during construction
        works correctly. Must all be the same else a ValueError should be
        raised."""
        Result(self.pmfs)
        Result(self.pmfs, self.pmfs2)
        self.pmfs[0].lambdas = np.linspace(0., 2., 16)
        with self.assertRaises(ValueError):
            Result(self.pmfs)
        with self.assertRaises(ValueError):
            Result(self.pmfs, self.pmfs2)

    def test_dG(self):
        """Test that expected free energy values are returned."""
        single_result = Result(self.pmfs)
        double_result = Result(self.pmfs, self.pmfs2)

        self.assertEqual(single_result.dG.value, self.pmf_values[-1]*2*0.05)
        self.assertEqual(double_result.dG.value,
                         self.pmf_values[-1]*6*0.05)

    def test_pmf(self):
        single_result = Result(self.pmfs)
        double_result = Result(self.pmfs, self.pmfs2)
        self.assertEqual(
            [round(fe.value, 8) for fe in single_result.pmf],
            [round(val*2*0.05, 8) for val in self.pmf_values])
        self.assertEqual(
            [round(fe.value, 8) for fe in double_result.pmf],
            [round(val*6*0.05, 8) for val in self.pmf_values])

    def test_negation(self):
        """Test use of negation operator"""
        single_result = Result(self.pmfs)
        double_result = Result(self.pmfs, self.pmfs2)
        self.assertEqual((-single_result).dG, -(single_result.dG))
        self.assertEqual((-double_result).dG, -(double_result.dG))

    def test_addition(self):
        """Test addition of Results objects"""
        single_result = Result(self.pmfs)
        double_result = Result(self.pmfs, self.pmfs2)

        self.assertEqual((single_result+single_result).dG.value,
                         single_result.dG.value*2)
        self.assertEqual((double_result+single_result).dG.value,
                         single_result.dG.value*4)


if __name__ == '__main__':
    unittest.main()
