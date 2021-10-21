# Job execution and farming scripts for MCCCS-MN
# Job farming workflow
### 1. Calculate system sizes
Before running GEMC adsorption simulations for a large number of nanoporous materials, the total number of adsorbate molecules for the simulations in each materials needs to be judiciously chosen. This is because a too small system size will deplete the vapor box, and a too large system size will result in large amounts of computation wasted in simulating the vapor box.

A rule of thumb is to **make the vapor box length at least 30 angstroms at the lowest temperture and highest pressure**. This can be done by
* Estimate the saturation loading either using a simulation with an ideal gas box at very high pressure and low temperature, or calculating from the pore volume (void fraction * unit cell volume * number of cells) of each zeolite and multiply it by the *liquid* density of the adsorbate.
* Add the number of ideal gas molecules at the lowest temperature and highest pressure in a 30-angstrom box to the saturation loading. This will become the total number of molecules for each material.

### 2. Preparing simulations
To generate the input files for all simulations in a farmed job, you will need to create the following "seed" files:

* A JSON configuration file `jobdata.json` specifying the zeolites, state points, and length for each job. An example `jobdata.json` file looks like below (note that JSON does not support comment, and the description after `#` is intended only for explanation in this document):
```yaml
{
    "cif": "/home/siepmann/sun00032/simulations/pcod/cifs", # location of zeolite structures
    "ztb": "/home/siepmann/sun00032/simulations/pcod/ztb", # location of zeolite structuretabulated potentials
    "exe": "/home/siepmann/exe-farm/src/topmon 1 1 1", # path to MCCCS-MN executable, including job-farming command line arguments
    "zeolites": "../pcod.txt", # file to the list of zeolites
    "pressures": [0.100, 0.271, 0.739, 2.009, 3.00, 5.460, 14.840, 40.340], # list of all pressures
    "temperatures": [77.00, 92.40, 110.88, 133.06, 159.67, 191.60, 229.92, 275.90], # list of all temperatures
    "n_indep": 4, # number of independent simulation
    "t_init": 3, # total length of initialization (volume relaxation) in hours
    "t_equil": 24, # total length of equilibration in hours
    "t_prod": 24, # total length of production in hours
    "max_walltime": 6, # maximum length of each job
    "arch": "HPE" # HPC architecture to generate job script
}
```
* A JSON file `ninit.json` containing the number of molecules to be initialized for each zeolite. A example `ninit.jsob` file looks like below:
```yaml
{
    "8056830": 1964,
    "8067418": 1357,
    "8078629": 1366,
    "8080784": 1154,
    ...
}
```
* A seed directory `seed/` which contains the template input files of a simulation. The `seed/` directory needs to contain two files at bare minimum: `topmon.inp` and `fort.4`. 
  * The `seed/topmon.inp` file is usually a symbolic link to a master `topmon.inp` file in the root directory of the job. Then all `topmon.inp` files in the farmed simulations will be linked to the same master file.
  * The `seed/fort.4` file will be copied and manipulated for each stage of the simulations.
* A text file containing the list of zeolites `zeolite.txt` is also usually created in the root directory.

Before generating input files for all simulations, the working directory will look like below:
```
.
├── jobdata.json
├── ninit.json
├── seed
│   ├── fort.4
│   └── topmon.inp
└── zeolites.txt
```
### 3. Generating simulation files
With a working directory with required files listed above, run
```bash
python /path/to/mcccs_proc/quickfarm/initialize.py
```
to create input files for all simulations.
After running the `initaialize.py` script, the working directory will look like:
```
.
├── jobdata.json
├── ninit.json
├── job.sh # job submission script
├── jobs # job list file to be used by MCCCS-MN
│   └── run1.txt
├── seed
│   ├── fort.4
│   └── topmon.inp
├── simulations # directories containing simulation inputs
│   └── ...
├── test # test directory for dry run
│   └── ...
└── zeolites.txt
```
### 4. Submitting batch jobs
Before running the large farmed job by `job.sh`, it is recommended to first perform a sanity check using the sample files produced in the `test/` directory to make sure there is no error in the simulation input files. To do this, simply run the MCCCS-MN job farming executable under the `test/` directory with 2 processes:
```bash
cd test
mpirun -n 2 /path/to/MCCCS-MN/topmon 1 1 1
cd ..
```
A successful test is marked by MCCCS-MN exiting without any errors (exit code 0).

Then the farmed job can be submitted to the job scheduler of the HPC cluster:
```bash
sbatch job.sh
```

### 5. Processing simulations between jobs
After a job is completed, use `quickfarm/next.py` to batch process all input files in a farmed job to the next round of simulations. Usage of the `next.py` script is:
```
python next.py [current_stage] [next_stage (optional)]
```
Choices of `current_stage` and `next_stage` arguments inlcude `init`, `equil`, and `prod`. When executing the script with only the first argument, the simulations of the farmed jobs will be kept in the same stage (initialization, equilibration or production), and the files generated from the last round will be stored in a directory named `init-$x`, `equil-$x`, or `prod-$x`, where `$x` will automatically increment if the simulations are kept in the same stage. When executing the script with two arguments, the simulations will be switched into the next stage, for example, from equilibration to production. The job count `$x` will be also restored to 1 for the next stage.

Before submitting a job after running `next.py`, **make sure that the file `jobs/done.txt` does not exist.** Otherwise the content in `jobs/done.txt` will be excluded in the next run.

### 6. Collecting data
After all simulations stages have completed, run `next.py prod` again to store the last round of simulation outputs into the `prod-$x` folder. 

Simulation outputs can be collected using a custom script, the `getData.py` file in Rob DeJaco's [MCFlow](https://github.com/dejac001/MCFlow), or the `readfort12`/`readfort12_mpi` scripts provided by this repository.

To use `readfort12` or `readfort12_mpi`, an additional file `run.txt` need to be created to specify the directories to collect data, then the executable is run in the root directory of the farmed job:
```bash
cp jobs/run1.txt runs.txt
mpirun -n 4 ./readfort12_mpi prod-1 prod-2 prod-3 [...]
```
The program will create a CSV file `fort12.csv` which contains ensemble averages for each simulation from the `fort.12` output file.
