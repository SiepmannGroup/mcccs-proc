# Job execution and farming scripts for MCCCS-MN
# Job farming workflow
### 1. Calculate system sizes
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
to create inout files for all simulations.
After running the `initaialize.py` script, the working directory will look like:
```
.
├── jobdata.json
├── ninit.json
├── job.sh
├── jobs
│   └── run1.txt
├── seed
│   ├── fort.4
│   └── topmon.inp
├── simulations
│   └── ...
├── test
│   └── ...
└── zeolites.txt
```
### 4. Submitting batch jobs

### 5. Processing simulations between jobs

### 6. Collecting data
