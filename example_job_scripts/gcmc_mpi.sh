#!/bin/bash
#SBATCH -N 1
#SBATCH -n 12
#SBATCH --job-name=protoms_gcmc_test
#SBATCH --time=07:00:00
#SBATCH --partition=compute
#SBATCH --output=protoms_gcmc_test.out  # Capture the standard output of your job to see what's going on/debug easier
#SBATCH --error=protoms_gcmc_test.err  # Capture the standard error output of your job to see what's going on/debug easier
#SBATCH --mail-user=FIRSTNAME.SURNAME@icr.ac.uk  # You can get email notifications for when your job starts/ends/failss
#SBATCH --mail-type=ALL

# Environment setup
. /data/scratch/DCT/UCCT/INSILICO/ProtoMS-ICR/protoms_env.sh

#OpenMP settings:
export OMP_NUM_THREADS=4
export OMP_PLACES=threads
export OMP_PROC_BIND=spread

echo "SLURM_STEP_NUM_TASKS: $SLURM_STEP_NUM_TASKS"
echo "OMP_NUM_THREADS: $OMP_NUM_THREADS"
echo "OMP_PLACES: $OMP_PLACES"
echo "OMP_PROC_BIND: $OMP_PROC_BIND"

srun --mpi=pmix --cpu_bind=cores $PROTOMSHOME/protoms3 run_gcmc.cmd
