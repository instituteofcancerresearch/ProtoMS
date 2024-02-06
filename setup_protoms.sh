#!/bin/bash

module use /opt/software/easybuild/modules/all
module load AmberTools
module load GCC/12.2.0
module load GCCcore/12.2.0
module load CMake/3.24.3-GCCcore-12.2.0

export PROTOMSHOME=/data/scratch/DCO/DIGOPS/SCIENCOM/kmarzouk/repos/ProtoMS-ICR
export AMBERHOME=/opt/software/easybuild/software/AmberTools/21-foss-2021a
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64

# source /data/scratch/DCO/DIGOPS/SCIENCOM/kmarzouk/repos/ProtoMS-ICR/venv/bin/activate

echo "PROTOMSHOME: $PROTOMSHOME"
echo "AMBERHOME: $AMBERHOME"
echo "PYTHON: $(which python)"
