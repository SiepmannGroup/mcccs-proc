import os, math, shutil
from subprocess import run, check_output
from mcccs_proc.file_io import read_fort4, read_restart

# aliases
pj = os.path.join
md = lambda p: os.makedirs(p, exist_ok=True)
mv = shutil.move

def safecp(scr, dst):
    if os.path.exists(scr):
        shutil.copy(scr, dst)
        return True
    return False


def read_inp_restart(f_in, f_restart):
    input_data = read_fort4(f_in)
    nmolty = int(input_data['&mc_shared']['nmolty'])
    nbox = int(input_data['&mc_shared']['nbox'])
    if os.path.exists(f_restart):
        restart_data = read_restart(f_restart, nmolty, nbox)
    else:
        restart_data = None
    return input_data, restart_data

def toint(s):
    return int(s.strip()) if type(s) == str else int(s)

def tofloat(s):
    return float(s.strip().rstrip('d0')) if type(s) == str else float(s)

def clean(data):
    for k, v in data.items():
        if type(v) == dict:
            clean(v)
        elif type(v) == str:
            data[k] = v.strip()

def avg_displacement(iline, *maxvalue):
    x, y, z = [float(x) for x in iline.split()]
    avgxyz = sum([x, y, z])/3
    if maxvalue and maxvalue[0] < avgxyz:
        print('average value too large: {}; changing to {}'.format(avgxyz, maxvalue[0]))
        avgxyz = maxvalue[0]
    myline = '  %f       %f       %f'%((avgxyz,)*3)
    return myline

def avg_print(nstep):
    iprint = math.ceil(nstep/10)
    if iprint > 1000:
        iblock = 1000
    else:
        iblock = iprint
    return iprint, iblock


def postprocess(name, workdir):
    MAX_BOX = 5
    cwd = os.getcwd()
    # Rob MCFlow convention
    os.chdir(os.path.join(workdir, name))
    os.rename('run1a.dat', 'run.%s' % name)
    os.rename('fort.4', 'fort.4.%s' % name)
    os.rename('fort.12', 'fort12.%s' % name)
    os.rename('config1a.dat', 'config.%s' % name)
    if os.path.exists("fort.77"):
        os.rename('fort.77', 'fort.77.%s' % name)
    for i in range(MAX_BOX):
        if os.path.exists('box%iconfig1a.xyz' % i):
            os.rename('box%iconfig1a.xyz' % i, 'box%iconfig.%s' % (i, name))
    os.chdir(workdir)
    if os.path.exists("fort.77"):
        os.remove("fort.77")
    os.rename("config1a.dat", "fort.77")
    os.chdir()

def store_run(name, workdir):
    MAX_BOX = 5
    # Rob MCFlow convention
    storedir = pj(workdir, name)
    md(storedir)
    safecp(pj(workdir, "fort.4"), pj(storedir, "fort.4.%s" % name))
    safecp(pj(workdir, "run1a.dat"), pj(storedir, "run.%s" % name))
    if not safecp(pj(workdir, "config1a.dat"), pj(storedir, "config.%s" % name)):
        safecp(pj(workdir, "save-config.1"), pj(storedir, "config.%s" % name))
        safecp(pj(workdir, "save-config.1"), pj(workdir, "config1a.dat"))
    safecp(pj(workdir, "fort.12"), pj(storedir, "fort12.%s" % name))
    if os.path.exists(pj(workdir, "fort.77")):
        mv(pj(workdir, "fort.77"), pj(storedir, "fort.77.%s" % name))
    for i in range(1, MAX_BOX + 1):
        if os.path.exists(pj(workdir, 'box%iconfig1a.xyz' % i)):
            os.rename(pj(workdir, 'box%iconfig1a.xyz' % i),
                     pj(storedir, 'box%iconfig.%s' % (i, name)))
    safecp(pj(workdir, "config1a.dat"), pj(workdir, "fort.77"))
    

'''
Calculates the scaling necessary for swap and swatch
moves to obtain NCACC accepted particle exchanges per cycle.
'''
def swap_scale(workdir, nbox, ncacc=1):
    res = check_output(['grep', "accepted = ", pj(workdir, "run1a.dat")])
    lines = res.decode('utf-8').strip().split("\n")
    n_accept = sum(float(l.split()[-1]) for l in lines)
    ncycles = int(check_output(['wc', '-l', pj(workdir, "fort.12")]).decode('utf-8').split()[0]) // nbox
    return ncycles / n_accept / ncacc



