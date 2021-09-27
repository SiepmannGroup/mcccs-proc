import os, sys, shutil
from mpi4py import MPI
from mcccs_proc.utils import store_run
from mcccs_proc.simulation import Simulation
from mcccs_proc.mpi import mpi_io
from mcccs_proc.quickfarm.next_movie import postprocess_farmed


if __name__ == "__main__":
    jobs = mpi_io.readlines("jobs/run1.txt")
    if len(sys.argv) <= 2:
        nextmode = None
    else:
        nextmode = sys.argv[2]
    if '-' in sys.argv[1]:
        mode = sys.argv[1].split('-')[0]
        run_num = int(sys.argv[1].split('-')[1])
    else:
        mode = sys.argv[1]
        run_num = 0
    store_key = postprocess_farmed(jobs, mode, nextmode=nextmode, run_num=run_num)
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    if rank == 0:
        os.makedirs("jobs/%s" % store_key)
        shutil.move("jobs/done.txt", "jobs/%s/done.txt" % store_key)
        shutil.move("jobs/log.txt", "jobs/%s/log.txt" % store_key)
