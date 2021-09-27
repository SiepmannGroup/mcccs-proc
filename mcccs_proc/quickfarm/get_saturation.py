import os, json
import numpy as np

jobfile = "jobs/run1.txt"
nbox = 2
ncycles = 10

with open(jobfile, 'r') as f:
    dirs = [l.strip() for l in f.readlines()]

data = []


def get_systemsize(n_sat):
    return int(n_sat) + 300

'''
# size is determined by number of H2 at lowest T, highest P
# in a 30*30*30 box
p = 4.034e7
T = 275.9
V = (3e-9) ** 3
k = 1.38064852e-23
z = 1.6
N = p * V / k / T / z = 179
# so add 250 molecules to get total size
'''

lines = []
lines.append('Path,n_sat,n_init\n')
ninit_dict = {}


for path in dirs:
    with open(os.path.join(path, 'fort.12'), 'r') as f:
        nmols = [int(l.strip().split()[-1]) for l in f.readlines()[-nbox * ncycles:]]
        n_zeo = nmols[::nbox]
        if sum(nmols[:nbox]) * ncycles != sum(nmols):
            raise ValueError("Incorrect total number of molecules")
        ninit = get_systemsize(np.mean(n_zeo))
        lines.append('%s,%.2f,%d\n' % (path, np.mean(n_zeo), ninit))
        ninit_dict[os.path.split(path)[-1]] = ninit
with open('n_sat.csv', 'w') as f:
    f.writelines(lines)

with open('ninit.json', 'w') as f:
    json.dump(ninit_dict, f)



