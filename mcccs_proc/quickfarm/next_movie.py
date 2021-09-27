import os, sys, shutil
from subprocess import call
from mcccs_proc.utils import store_run, swap_scale
from mcccs_proc.simulation import Simulation
from mcccs_proc.calc_imv import calc_imv

def postprocess_farmed(jobs, mode, nextmode=None, run_num=0, set_movie=True):
    if mode not in ["init", "equil", "prod"]:
        raise ValueError("mode not understand! use init, equil or prod")
    if nextmode and nextmode not in ["init", "equil", "prod"]:
        raise ValueError("mode not understand! use init, equil or prod")
    # first check how many runs are done by folders
    if run_num <= 0:
        for o in os.listdir(jobs[0]):
            if os.path.isdir(os.path.join(jobs[0], o)) and mode in o:
                try:
                  run_num = max(run_num, int(o.split('-')[1]))
                except ValueError:
                    print("directory named %s with no run number, skipped" % o)
    else:
        run_num -= 1
    # the current run is (mode)-(run_num+1)
    store_key = "%s-%d" % (mode, run_num + 1)
    for i, path in enumerate(jobs):
        # stores previous run
        store_run(store_key, path)
        has_prod = False
        # copy input file for next run
        if nextmode:
            if os.path.exists(os.path.join(path, "fort.4.%s-1" % nextmode)):
                shutil.copy(os.path.join(path, "fort.4.%s-1" % nextmode),
                            os.path.join(path, "fort.4" )
                            )
                has_prod = True
            elif os.path.exists(os.path.join(path, "fort.4.%s" % nextmode)):
                shutil.copy(os.path.join(path, "fort.4.%s" % nextmode),
                            os.path.join(path, "fort.4" ))
                has_prod = True
        elif mode != 'prod':
            if os.path.exists(os.path.join(path, "fort.4.%s-%d" % (mode, run_num + 2))):
                shutil.copy(os.path.join(path, "fort.4.%s-%d" % (mode, run_num + 2)),
                            os.path.join(path, "fort.4" )
                            )
        if nextmode == 'prod':
            sim = Simulation(path)
            if not has_prod:
                sim.disable_displacement_change()
                sim.enable_pressure_calc(5)
                sim.set_allow_cutoff_failure(-1)
            scale = swap_scale(path, sim.nbox())
            if set_movie:
                imv = calc_imv(os.path.join(path, 'fort.12'), nbox=sim.nbox())
                if imv == 200000:
                    print("no loading at", path)
            for i in range(1, sim.nbox()):
                boxl = sum(sim.get_boxlength(i)) / 3
                if boxl <= 30:
                    print("Warning: job at %s has a too small vapor box of %.3f angstroms." % (path, boxl))
                new_cut = 0.35 * boxl
                if new_cut < 14 and boxl > 30:
                    new_cut = 14
                sim.set_rcut(new_cut, i)
            sim.flat_displacement()
            sim.scale_swap_prob(scale)
            if set_movie:
                sim._set("imv", imv)
            sim.apply()
        ## remove run1a.dat, fort.12 and config1a.dat
        #if os.path.exists(os.path.join(path, 'run1a.dat')):
        #    os.remove(os.path.join(path, 'run1a.dat'))
        #if os.path.exists(os.path.join(path, 'config1a.dat')):
        #    os.remove(os.path.join(path, 'config1a.dat'))
        #
        if i > 0 and i % 256 == 0:
            print("done %d runs" % i)
    return store_key


if __name__ == "__main__":
    with open("jobs/run1.txt", 'r') as f:
        jobs = [l.strip() for l in f.readlines()]
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
    #os.makedirs("jobs/%s" % store_key)
    #shutil.move("jobs/done.txt", "jobs/%s/done.txt" % store_key)
    #shutil.move("jobs/log.txt", "jobs/%s/log.txt" % store_key)

