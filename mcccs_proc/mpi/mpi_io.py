from mpi4py import MPI

'''
Read a file and distribute the lines
in the file to all MPI ranks, including the master rank.
Lines are stripped after reading.
'''
def readlines(path):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    buffer = None
    if rank == 0:
        chunks = comm.Get_size()
        buffer = [[] for i in range(chunks)]
        with open(path, 'r') as f:
            for i, l in enumerate(f.readlines()):
                buffer[i % chunks].append(l.strip())
    buffer = comm.scatter(buffer, root=0)
    return buffer





