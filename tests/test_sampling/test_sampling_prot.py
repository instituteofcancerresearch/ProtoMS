"""This test is to check the Sampling MC moves."""

import nose
import unittest
import argparse
import os
import sys
import subprocess
import logging
import time
import re
import numpy as np
import protoms

from protoms import _is_float, _get_prefix, _locate_file, _merge_templates, _load_ligand_pdb, _prep_ligand, _prep_protein, _prep_singletopology, _prep_gcmc, _prep_jaws2, _cleanup, _wizard

import tools
from tools import simulationobjects

from subprocess import call

#---------------------------------------------
# ProtoMS Equilibration Sampling MC moves test
#---------------------------------------------

# Storing PROTOMSHOME environment variable to a python variable.
proto_env = os.environ["PROTOMSHOME"]
test_dir = proto_env + "/tests/test_sampling/"
ref_dir = proto_env + "/tests/sampling/"
output_files_setup = ["dcb.prepi", "dcb.frcmod", "dcb.zmat", "dcb.tem", "dcb_box.pdb", "protein_scoop.pdb", "water.pdb", "run_bnd.cmd"]
out_sim_files = ["info", "all.pdb", "warning", "results", "restart.prev", "restart", "accept"]
outfiles = ["dcb.prepi", "dcb.frcmod", "dcb.zmat", "dcb.tem", "dcb_box.pdb", "protein_scoop.pdb", "run_bnd.cmd"]

class TestSampling(unittest.TestCase):
    
    """Test for Sampling function."""

    def setUp(self):
        super(TestSampling, self).setUp()

    def tearDown(self):
        super(TestSampling, self).tearDown()

    def test_sampling(self):
        
        """ Test for Sampling function."""
        
        if((call("python2.7 $PROTOMSHOME/protoms.py -s sampling -l dcb.pdb -p protein.pdb --nequil 0 --nprod 100 --ranseed 100000 --dumpfreq 10 -f" + test_dir, shell=True)) == 0):

            """Checking whether the required output files have been setup for Sampling MC moves."""
                
            for out_files in output_files_setup:
                self.assertTrue(os.path.exists(test_dir + out_files), "ProtoMS setup output file %s is missing. There could be problems with zmat generation, forcefield issues and ProtoMS input command file generation for simulation." % (test_dir + out_files))

            """Checking content of setup output files with reference data in files."""
            
            for out_files in outfiles:
                if((call("diff "+ test_dir + out_files + " "+ ref_dir + out_files, shell=True)) == 0):
                    continue
                else:
                    raise ValueError("Content mismatch between output and reference %s" %(out_files))
  
        else:
            raise simulationobjects.SetupError("ProtoMS setup for sampling MC moves is not successful!")

        if((call("$PROTOMSHOME/protoms3 run_bnd.cmd", shell=True)) == 0):

            """Checking whether the simulation output files have been created successfully for Sampling MC moves."""
            for out_files in out_sim_files:
                self.assertTrue(os.path.exists("out_bnd/"+ out_files), "Sampling simulation file: %s is missing." % out_files )

                """Checking content of sampling MC moves output files with reference data in files."""
                if out_files == "info":
                   if((call("bash "+ test_dir+"content_info_comp.sh", shell=True)) == 0):
                       continue
                   else:
                       raise ValueError("Content mismatch between output and reference info file.")
                else:
                    if((call("diff " + test_dir + "out_bnd/" + out_files + " "+ ref_dir+"out_bnd/" + out_files, shell=True)) == 0):
                        continue
                    else:
                        raise ValueError("Content mismatch between output and reference %s" %(os.path.join(test_dir,"out_bnd/", out_files)))
            
        else:
            raise simulationobjects.SetupError("Sampling MC protoms simulation failed!")

#Entry point for nosetests or unittests

if __name__ == '__main__':
    unittest.main()
    nose.runmodule()

