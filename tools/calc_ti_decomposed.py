from collections import defaultdict
from itertools import chain
import matplotlib
import numpy as np
import os
import free_energy_base as feb

if "DISPLAY" not in os.environ or os.environ["DISPLAY"] == "":
    matplotlib.use('Agg')
import matplotlib.pyplot as plt


class TI_decomposed(feb.Estimator):
    """Estimate free differences using ThermodynamicIntegration. The class
    performs individual calculations for each component of the system
    interaction and internal energies. Results from each component
    will sum to give the same result as the total energy. The
    decomposition of the total free energy is not well-defined however
    can be indicative of the dominant terms in a free energy change.
    """
    def __init__(self, lambdas):
        self.estimators = defaultdict(lambda: feb.TI(lambdas))
        self.lambdas = lambdas

    def add_data(self, series):
        """Save data from a SnapshotResults.series object
        for later calculation"""
        dlam = series.lamf[0]-series.lamb[0]
        min_len = 10E20
        for name, term in series.interaction_energies.iteritems():
            for energy in term[:-1]:
                dat = (energy.forw-energy.back) / dlam
                min_len = len(dat) if len(dat) < min_len else min_len
                self.estimators["%s_%s" % (name, energy.type)].data.append(dat)

        for name, term in series.internal_energies.iteritems():
            for energy in term[:-1]:
                dat = (energy.forw-energy.back) / dlam
                min_len = len(dat) if len(dat) < min_len else min_len
                self.estimators["%s_%s" % (name, energy.type)].data.append(dat)

        return min_len

    def calculate(self, subset=(0., 1., 1)):
        """Calculate the free energy difference for each energy component and
        return a dictionary of PMF objects."""
        return {term: self.estimators[term].calculate(subset)
                for term in self.estimators}

    def __getitem__(self, val):
        new_est = self.__class__(self.lambdas)
        for term in self.estimators:
            new_est.estimators[term] = self.estimators[term][val]
        return new_est

    def __len__(self):
        lengths = [dat.shape[-1] for term in self.estimators
                   for dat in self.estimators[term].data]
        if len(lengths) == 0:
            return 0
        if len(set(lengths)) > 1:
            raise Exception("Found data entries of different lengths.")
        return lengths[0]


class DecomposedCalculation(feb.FreeEnergyCalculation):
    def __init__(self, root_paths):
        # temperature can be given as zero as TI estimators do
        # not make use of it
        feb.FreeEnergyCalculation.__init__(
            self,
            root_paths=root_paths,
            temperature=0.,
            estimators={feb.TI, TI_decomposed})

    def calculate(self, subset=(0., 1., 1.)):
        results = {}

        results[feb.TI] = feb.Result(
            [rep.subset(*subset).calculate(self.temperature)
             for rep in self.estimators[feb.TI]])

        # dealing with the decomposed estimator is a little more difficult
        # repeats for the same term need to be grouped together into a
        # single Results object
        # start by pulling out all the data
        data = []
        for rep in self.estimators[TI_decomposed]:
            data.append(rep.subset(*subset).calculate(self.temperature))

        # now add into results in a compatible order such that
        # results[TI_decomposed][term] = Results object
        results[TI_decomposed] = {}
        for term in data[0]:
            results[TI_decomposed][term] = feb.Result(
                [rep[term] for rep in data]
            )

        return results

    def _body(self, args):
        subset = (args.lower_bound, args.upper_bound)
        results = self.calculate(subset=subset)
        decomp = results[TI_decomposed]

        if (args.bound or args.gas) is not None:
            calc2 = DecomposedCalculation(args.bound or args.gas)
            results2 = calc2.calculate(subset=subset)
            decomp2 = results2[TI_decomposed]

            # iterate over the unique keys from both calc and calc2
            for term in set(chain(decomp, decomp2)):
                try:
                    decomp[term] -= decomp2[term]
                except KeyError:
                    decomp[term] = -decomp2[term]
                if args.bound is not None:
                    decomp[term] = -decomp[term]

            # update standard TI result as well
            results[feb.TI] -= results2[feb.TI]
            # swap the sign if this is a binding calculation
            if args.bound is not None:
                results[feb.TI] = -results[feb.TI]

        if args.dualtopology:
            consolidate_terms(decomp)
        self.figures['decomposed'], _ = plot_terms(decomp)

        if args.pmf:
            self.figures['decomposed_pmf'], _ = plot_pmfs(decomp)

        print "%20s:" % "FDTI", results[feb.TI].dG
        print

        for term in sorted(decomp):
            print "%20s:" % term, decomp[term].dG
        print "%20s:" % "sum of terms", np.sum(decomp.values()).dG

        return results


def consolidate_terms(data):
    # this is currently not robust to inclusion of gcsolute terms
    # and just generally horrible
    for i in ('COU', 'LJ'):
        solvent_interaction_terms = []
        for term in data:
            if "-solvent" in term and i in term:
                if "protein" not in term and "solvent-solvent" not in term:
                    solvent_interaction_terms.append(term)
        if len(solvent_interaction_terms) > 1:
            data['lig-solvent_%s' % i] = np.sum(
                [data.pop(term) for term in solvent_interaction_terms])

        protein_interaction_terms = []
        for term in data:
            if "protein1-" in term and i in term:
                if "solvent" not in term:
                    protein_interaction_terms.append(term)
        if len(protein_interaction_terms) > 1:
            data['protein1-lig_%s' % i] = np.sum(
                [data.pop(term) for term in protein_interaction_terms])


def plot_terms(data):
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.3)

    ys, errs, labels = [], [], []
    for term in sorted(data):
        dG = data[term].dG
        # only include terms with non-zero differences
        if dG.value != 0.:
            ys.append(dG.value)
            errs.append(dG.error)
            labels.append(term)

    xs = np.arange(len(ys))
    ax.bar(xs, ys, yerr=errs, ecolor='black')
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation="vertical")
    return fig, ax


def plot_pmfs(data):
    fig, ax = plt.subplots()
    for term in data:
        if data[term].dG.value != 0.:
            data[term].pmf.plot(ax, label=term)
    ax.legend(loc='best')
    return fig, ax


def get_arg_parser():
    """Add custom options for this script"""
    parser = feb.FEArgumentParser(
        description="Calculate individual contributions of different terms "
                    "to the total free energy difference. Although terms are "
                    "guaranteed to be additive with TI, the decomposition "
                    "is not strictly well defined. That said, it can be "
                    "illustrative to consider the dominant contributions of "
                    "a calculation.",
        parents=[feb.get_arg_parser()])
    parser.add_argument("-b", "--bound", nargs="+",
                        help="Output directories of bound phase calculations. "
                             "If present, it is assumed that -d "
                             "provides solvent phase simulation data.",
                        clashes=['gas'])
    parser.add_argument("-g", "--gas", nargs="+",
                        help="Output directories of gas phase calculations. "
                             "If present, it is assumed that -d "
                             "provides solvent phase simulation data.",
                        clashes=['bound'])
    parser.add_argument("-o", "--out", type=str, default="decomposed.pdf",
                        help="Filename of output graph.")
    parser.add_argument("--dualtopology", action='store_true', default=False,
                        help="Indicates provided data is from a dual topology"
                             "calcalution. Attempts to consolidate terms "
                             "from ligands for clarity that can have opposite "
                             " sign and large magnitudes.")
    parser.add_argument("--pmf", action='store_true', default=False,
                        help="Plot the pmf of the individual terms.")
    return parser


if __name__ == "__main__":
    args = get_arg_parser().parse_args()
    calc = DecomposedCalculation(args.directories)
    calc.run(args)
