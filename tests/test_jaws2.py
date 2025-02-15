import unittest

import framework


class Jaws2SetupTest(framework.BaseTest):
    ref_dir = "tests/jaws2/"

    input_files = [
        "fragment.pdb",
        "protein.pdb",
        "jaws2_waters.pdb",
        "water.pdb",
    ]

    executable = "protoms.py"

    args = [
        "-s",
        "jaws2",
        "-l",
        "fragment.pdb",
        "-p",
        "protein.pdb",
        "--gcmcwater",
        "jaws2_waters.pdb",
        "--jawsbias",
        "8",
        "10",
        "12",
        "14",
        "--nequil",
        "0",
        "--nprod",
        "100",
        "--ranseed",
        "100000",
        "--setupseed",
        "100000",
        "--dumpfreq",
        "10",
        "--gaff",
        "gaff14",
    ]

    output_files = [
        "fragment.prepi",
        "fragment.frcmod",
        "fragment.tem",
        "fragment.zmat",
        "fragment_box.pdb",
        "protein_scoop.pdb",
        "jaws2_wat1.pdb",
        "jaws2_wat2.pdb",
        "jaws2_wat3.pdb",
        "jaws2_not1.pdb",
        "jaws2_not2.pdb",
        "jaws2_not3.pdb",
        "run_jaws2-w1_jaws.cmd",
        "run_jaws2-w2_jaws.cmd",
        "run_jaws2-w3_jaws.cmd",
    ]


class Jaws2SimulationTest(framework.BaseTest):
    ref_dir = "tests/jaws2/"

    input_files = [
        "run_jaws2-w1_jaws.cmd",
        "jaws2_wat1.pdb",
        "fragment.pdb",
        "water.pdb",
        "jaws2_not1.pdb",
        "fragment.tem",
        "protein_scoop.pdb",
    ]

    mpi_processes = 4

    executable = "build/protoms3"

    args = ["run_jaws2-w1_jaws.cmd"]

    output_directories = [
        "out_jaws2-w1/j_+8.000",
        "out_jaws2-w1/j_+10.000",
        "out_jaws2-w1/j_+12.000",
        "out_jaws2-w1/j_+14.000",
    ]

    output_files = [
        "accept",
        "all.pdb",
        "info",
        "restart",
        "restart.prev",
        "results",
        "warning",
    ]


if __name__ == "__main__":
    unittest.main()
