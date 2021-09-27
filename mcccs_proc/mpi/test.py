import sys, mpi_io

lines = mpi_io.readlines("test.txt")
print(sys.argv)
print(lines)