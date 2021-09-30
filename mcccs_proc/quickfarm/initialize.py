import os, sys, shutil, json, math
from subprocess import call
sys.path.append('/home/asunumn/scripts')
from mcccs_proc.preprocess import setup, initialize_2box

T_RELAX_MIN = 10
seed_path = "seed"

def make_simulation(path, z, p, t, k, jobdata, initdata, testmode=False):
    nstep = 1 if testmode else NSTEP
    rholiquid = jobdata["rhol"] if "liquid" in jobdata and [p, t] in jobdata["liquid"] else -1
    os.makedirs(path)
    for f in os.listdir(seed_path):
        shutil.copy(os.path.join(seed_path, f), os.path.join(path, f), follow_symlinks=False)
    initialize_2box(path, t, p, initdata[z], rholiquid)
    if jobdata["t_init"] > 0:
        # set equil-1 (volume step)
        t_init = min(jobdata["t_init"], jobdata["max_walltime"] - T_RELAX_MIN / 60)
        setup(path, nstep, k, "equil", time=t_init*3600,
             vol=0.1, swap=0, swatch=pswatch, cbmc=pcb, rotation=rot, rcut=0.5, other=["linit=T"])
        shutil.copy(os.path.join(path, "fort.4"), os.path.join(path, "fort.4.init"))
    n_equil = int(round(jobdata["t_equil"] / jobdata["max_walltime"]))
    tminus = jobdata["t_equil"]
    for i in range(1, n_equil + 1):
        init = "T" if jobdata["t_init"] == 0 and i == 1 else "F"
        t_equil = min(tminus, jobdata["max_walltime"] - T_RELAX_MIN / 60)
        setup(path, nstep, k, "equil", time=t_equil*3600,
            vol='auto', swap=0.1, swatch=pswatch, cbmc=pcb, rotation=rot, rcut=0.4, other=["linit=%s" % init])
        tminus -= jobdata["max_walltime"]
        shutil.copy(os.path.join(path, "fort.4"), os.path.join(path, "fort.4.equil-%d" % i))
        init = "F"
    n_prod = int(round(jobdata["t_prod"] / jobdata["max_walltime"]))
    tminus = jobdata["t_prod"]
    for i in range(1, n_prod + 1):
        t_prod = min(tminus, jobdata["max_walltime"] - T_RELAX_MIN / 60)
        setup(path, nstep, k, "prod", time=t_equil*3600,
            vol='auto', swap=0.1, swatch=pswatch, cbmc=pcb, rotation=rot, rcut=0.4, other=["linit=F"])
        tminus -= jobdata["max_walltime"]
        shutil.copy(os.path.join(path, "fort.4"), os.path.join(path, "fort.4.prod-%d" % i))
    # copy back fort.4.init
    if jobdata["t_init"] > 0:
        shutil.copy(os.path.join(path, "fort.4.init"), os.path.join(path, "fort.4"))
    else:
        shutil.copy(os.path.join(path, "fort.4.equil-1"), os.path.join(path, "fort.4"))
    if os.path.exists(os.path.join(jobdata["cif"], "%s.cif" % z)):
        os.symlink(os.path.join(jobdata["cif"], "%s.cif" % z), os.path.join(path, "zeolite.cif"))
    elif os.path.exists(os.path.join(jobdata["cif"], "%s.pdb" % z)):
        os.symlink(os.path.join(jobdata["cif"], "%s.pdb" % z), os.path.join(path, "zeolite.pdb"))
        os.remove(os.path.join(path, "topmon.inp"))
        os.symlink(os.path.join(seed_path, "topmon_pdb.inp"), os.path.join(path, "topmon.inp"))
    else:
        raise FileNotFoundError("Zeolite structure file does not exist")
    os.symlink(os.path.join(jobdata["ztb"], "%s.ztb" % z), os.path.join(path, "zeolite.ztb"))

def generate_script(jobs, jobdata):
    lines = []
    # one master rank in addition to simulations
    njobs = len(jobs) + 1
    # Cray XC40 on ALCF Theta, qsub + aprun
    # 64 cores/node
    if jobdata["arch"] == "XC40":
        NCORES = 64
        lines.append('#!/bin/bash\n')
        lines.append('#COBALT -t %d\n' % (jobdata["max_walltime"] * 60))
        n_nodes = math.ceil(njobs / NCORES)
        lines.append('#COBALT -n %d\n' % n_nodes)
        lines.append('#COBALT -A NanoReactive_3\n\n')
        lines.append('aprun -n %d -N %d %s' % (njobs, NCORES, jobdata["exe"]))
    # Cray XC40 on ALCF Theta, qsub + aprun
    # 64 cores/node
    elif jobdata["arch"] == "MSI":
        NCORES = 128
        lines.append('#!/bin/bash\n')
        lines.append('#SBATCH --time=%d:00:00\n' % jobdata["max_walltime"])
        lines.append('#SBATCH --ntasks %d\n' % njobs)
        lines.append('#SBATCH --cpus-per-task=1\n')
        lines.append('#SBATCH --ntasks-per-node=%d\n' % NCORES)
        lines.append('srun %s' % jobdata["exe"])
    else:
        raise NotImplementedError("Unknown architecture!")
    with open("job.sh", 'w') as f:
        f.writelines(lines)
    call(["chmod", "+x", "job.sh"])




with open('jobdata.json', 'r') as f:
    jobdata = json.load(f)

with open(jobdata["zeolites"], 'r') as f:
    zeolites = [l.strip() for l in f.readlines()]
jobdata["zeolites"] = zeolites

with open('ninit.json', 'r') as f:
    initdata = json.load(f)   

print("Initializing %d zeolites, %d state points, %d independent simulations" \
        % (len(jobdata["zeolites"]), len(jobdata["temperatures"]) * len(jobdata["pressures"]),
            jobdata["n_indep"]))

if "liquid" in jobdata:
    print("%d state points will be initialized as liquid" % len(jobdata["liquid"]))
    print("Liquid density is %f mol/L" % jobdata["rhol"])

os.makedirs("simulations")


pswatch = jobdata.get("swatch", 0)
pcb = jobdata.get("cbmc", 0)
rot = jobdata.get("rotation_dof", 2)
NSTEP = jobdata.get("max_step", 200000)
# may also input pressure grid as relative to saturated vapor pressure 
# at each temperature
if "p_sat" in jobdata:
    psat = jobdata["p_sat"]
else:
    psat = None

# make a test simulation
make_simulation("test/run", jobdata['zeolites'][0], jobdata['pressures'][0], jobdata['temperatures'][0], 0, jobdata, initdata, testmode=True)
os.makedirs("test/jobs")
with open("test/jobs/run1.txt", 'w') as f:
    f.write("run\n")



jobs = []
ncur = 0
for z in jobdata['zeolites']:
    for ipres, p in enumerate(jobdata['pressures']):
        for itemp, t in enumerate(jobdata['temperatures']):
            for k in range(1, jobdata['n_indep'] + 1):
                p_real = psat[itemp] * p if psat else p
                path = os.path.join("simulations", "%s-P%d-T%d" % (z, ipres, itemp), str(k))
                jobs.append(path + '\n')
                make_simulation(path, z, p_real, t, k, jobdata, initdata)
                ncur += 1
                if ncur % 1024 == 0 and ncur > 0:
                    print("created %d runs" % (ncur))
# write submission script
generate_script(jobs, jobdata)
                
os.makedirs("jobs")
with open("jobs/run1.txt", 'w') as f:
    f.writelines(jobs)
                
