import os, sys, shutil
from mcccs_proc.utils import store_run
from mcccs_proc.simulation import Simulation
from next_movie import postprocess_farmed

if __name__ == "__main__":
    with open("jobs/run1.txt", 'r') as f:
        jobs = [l.strip() for l in f.readlines()]
    if len(sys.argv) <= 2:
        nextmode = None
    else:
        nextmode = sys.argv[2]
    postprocess_farmed(jobs, sys.argv[1], nextmode=nextmode, set_movie=False)
