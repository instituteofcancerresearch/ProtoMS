import matplotlib
import numpy as np
import os
import sys
from protomslib import free_energy as fe

# from gcmc_free_energy_base import GCMCMBAR

if "DISPLAY" not in os.environ or os.environ["DISPLAY"] == "":
    matplotlib.use("Agg")
import matplotlib.pyplot as plt


class FreeEnergyCalculation(fe.FreeEnergyCalculation):
    """Perform a basic free energy calculation."""

    def test_equilibration(self, discard_limit):
        """Perform a series of calculations discarding increasing portions
        from the start of the loaded data series. This assesses whether
        unequilibrated data from the start of a simulation is biasing
        the result.

        Parameters
        ----------
        discard_limit : float
          Value between 0 and 1 that indicates the maximum amount of
          data to discard. E.g. a value of 0.2 would perform a series
          of calculations that range between using all of available
          data and the last 80% of the data.
        """
        proportions = np.linspace(0.0, discard_limit, 10)
        return {
            prop: self.calculate(subset=(prop, 1.0)) for prop in proportions
        }

    def test_convergence(self, discard_limit, lower_limit=0.0):
        """Perform a series of calculations discarding increasing portions
        from the end of the loaded data series. This assesses whether
        sufficient data has been sampled to produce converged free energy
        estimates.

        Parameters
        ----------
        discard_limit : float
          Value between 0 and 1 that indicates the minimum proportion of data
          to use. E.g. a value of 0.8 would perform a series of calculations
          that range between using the all of the available data and the first
          80% of the data.
        lower_limit : float, optional
          Specifies an initial proportion of the data set to discard from all
          calculations. Allows unequilibrated data to be removed.
        """
        proportions = np.linspace(discard_limit, 1.0, 10)
        return {
            prop: self.calculate(subset=(lower_limit, prop))
            for prop in proportions
        }

    def _body(self, args):
        """Calculation business logic.

        Parameters
        ----------
        args: argparse.Namespace object
            Namespace from argumentparser
        """
        if (args.test_equilibration or args.test_convergence) is not None:
            if (args.test_equilibration) is not None:
                results = self.test_equilibration(args.test_equilibration)
            else:
                results = self.test_convergence(
                    args.test_convergence, lower_limit=args.lower_bound
                )
            fig = plot_fractional_dataset_results(results, self.estimators)
            figname = "equil" if args.test_equilibration else "convergence"
            self.figures[figname] = fig
        else:
            results = self.calculate(
                subset=(args.lower_bound, args.upper_bound)
            )
            if args.pmf:
                self.figures["pmf"] = plot_pmfs(results)

            self.tables.extend(make_result_tables(args.directories, results))
        return results


def plot_results(x, results, axes, **kwargs):
    """Plot the free energy differences from a collection of result objects.

    Parameters
    ----------
    x : list (or other sequence) of numbers
      the x-axis values
    results : list (or other sequence) of Result objects
      the free energy results to plot
    axes : a matplotlib.Axes object
      the axes to plot on
    **kwargs :
      all additional keyword arguments are passed to axes.plot()
    """
    y = np.array([result.dG.value for result in results])
    err = np.array([result.dG.error for result in results])

    line = axes.plot(x, y, **kwargs)[0]
    axes.plot(x, y + err, "--", linewidth=1, color=line.get_color())
    axes.plot(x, y - err, "--", linewidth=1, color=line.get_color())


def plot_fractional_dataset_results(results, estimators):
    """Plot results of calculations that use variable portions of available
    data i.e. equilibration and convergence tests.

    Parameters
    ----------
    results : dict of float-(dict of Estimator class-Result object pairs)
      results to plot, keys are used as the x-values
    estimators : list (or other sequence) of Estimator classes
      Estimator classes used to store
    """
    fig, ax = plt.subplots()
    x = sorted(results)
    for estimator in estimators:
        dat = [results[prop][estimator] for prop in x]
        plot_results(x, dat, ax, label=estimator.__name__)
    ax.legend(loc="best")
    ax.set_xlabel("Proportion")
    ax.set_ylabel("Free energy (kcal/mol)")
    return fig


def plot_pmfs(results):
    """Plot average potentials of mean force for all (1d) estimators.

    Parameters
    ----------
    results : dict of Estimator class-Result object pairs
      the results to plot"""
    fig, ax = plt.subplots()
    for estimator in sorted(results, key=lambda i: i.__name__):
        results[estimator].pmf.plot(ax, label=estimator.__name__)
    ax.legend(loc="best")
    return fig


def make_result_tables(directories, results):
    """Print calculated free energies. If multiple repeats are present
    the mean and standard error are also printed.

    Parameters
    ----------
    directories : list of list (or other sequences) of strings
      the directory name associated with each result
    results : dict of Estimator class-Result object pairs
    """
    tables = []
    for estimator in sorted(results, key=lambda x: x.__name__):
        table = fe.Table(estimator.__name__, ["%s", "%.2f"])
        for i, result in enumerate(results[estimator].data):
            dGs = []
            for j, pmf in enumerate(result):
                dGs.append(pmf.dG)
                table.add_row([directories[i][j], pmf.dG.value])
            table.add_row(["Mean", fe.Quantity.fromData(dGs)])
            table.add_blank_row()
        table.add_row(["Total Mean", results[estimator].dG])
        tables.append(table)
    return tables


def get_arg_parser():
    """Returns the custom argument parser for this script"""
    parser = fe.FEArgumentParser(
        description="Calculate free energy differences using a range of"
        " estimators",
        parents=[fe.get_alchemical_arg_parser()],
    )
    parser.add_argument(
        "--pmf",
        action="store_true",
        default=False,
        help="Make graph of potential of mean force",
        clashes=("test_convergence", "test_equilibration"),
    )
    parser.add_argument(
        "--test-equilibration",
        default=None,
        type=float,
        help="Perform free energy calculations 10 times using varying "
        "proportions of the total data set provided. Data used will "
        "range from 100%% of the dataset down to the proportion "
        "provided to this argument",
        clashes=("test_convergence", "lower_bound"),
    )
    parser.add_argument(
        "--test-convergence",
        default=None,
        type=float,
        help="Perform free energy calculations 10 times using varying "
        "proportions of the total data set provided. Data used will "
        "range from 100%% of the dataset up to the proportion "
        "provided to this argument",
    )
    parser.add_argument(
        "--estimators",
        nargs="+",
        default=["ti", "mbar", "bar"],
        choices=["ti", "mbar", "bar", "gcap"],
        help="Choose free energy estimator to use. By default TI, BAR and MBAR"
        " are used. Note that the GCAP estimator assumes a different file"
        " structure and ignores the --subdir flag.",
    )
    parser.add_argument(
        "-v",
        "--volume",
        type=float,
        default=None,
        help="Volume of GCMC region",
    )
    return parser


def run_script(cmdline):
    """Execute the script, allows for straight-forward testing."""
    class_map = {
        "ti": fe.TI,
        "mbar": fe.MBAR,
        "bar": fe.BAR,
        "gcap": fe.GCMCMBAR,
    }
    args = get_arg_parser().parse_args(cmdline)
    calc = FreeEnergyCalculation(
        root_paths=args.directories,
        temperature=args.temperature,
        subdir=args.subdir,
        estimators=list(map(class_map.get, args.estimators)),
        volume=args.volume,
        results_name=args.name,
    )
    calc.run(args)


if __name__ == "__main__":
    run_script(sys.argv[1:])
