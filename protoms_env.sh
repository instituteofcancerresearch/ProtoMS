#!/bin/bash

# Load modules
module use /opt/software/easybuild/modules/all
module load AmberTools
module load GCC/12.2.0
module load GCCcore/12.2.0
module load CMake/3.24.3-GCCcore-12.2.0

# This causes havoc in an actual environment build
module unload SciPy-bundle/2021.05-foss-2021a

# Extract directory "this" script lives in
CURRENT_DIR="$(dirname -- "${BASH_SOURCE[0]}")" # relative
CURRENT_DIR="$(cd -- "$CURRENT_DIR" && pwd)" # absolute and normalized
if [[ -z "$CURRENT_DIR" ]] ; then
  exit 1
fi

# Set ProtoMS and Amber directory paths
export PROTOMSHOME=$CURRENT_DIR # /data/scratch/DCO/DIGOPS/SCIENCOM/kmarzouk/repos/ProtoMS-ICR
export AMBERHOME=/opt/software/easybuild/software/AmberTools/21-foss-2021a

# Append to help find standard symbols
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64

# Standardize sourcing of virtualenv
function activate_venv {
  source "$PROTOMSHOME/venv/bin/activate"
}

# Create environment, upgrade pip & install requirements
if [ ! -d "$PROTOMSHOME/venv" ]; then
  python -m venv "$PROTOMSHOME/venv"
  activate_venv
  pip install --upgrade pip
  pip install -r requirements.txt
else
  activate_venv
fi

# Echo summary of variables
echo "PROTOMSHOME: $PROTOMSHOME"
echo "AMBERHOME: $AMBERHOME"
echo "PYTHON: $(which python)"

# Add protoms path to path
export PATH=$PATH:$PROTOMSHOME
