# Job execution and farming scripts for MCCCS-MN
# Job farming workflow
### Preparing simulations
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
    "t_init": 3, # total length of initialization/melting in hours
    "t_equil": 24, # total length of equilibration in hours
    "t_prod": 24, # total length of production in hours
    "max_walltime": 6, # maximum length of each job
    "arch": "HPE" # HPC architecture to generate job script
}
```

### Submitting batch jobs

### Processing simulations between jobs

### Collecting simulation data
