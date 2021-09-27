from simulation import Simulation

MCRUN = 'python /home/andrewsun/scripts/mcccs_proc/runner.py'
POST = 'python /home/andrewsun/scripts/mcccs_proc/postprocess.py'

def setup(job, zeolite=False):
    job.add_input('fort.4')
    job.add_input('topmon.inp')
    job.add_checkpoint('fort.77')
    for f in ['run1a.dat', 'config1a.dat', 'fort.12', 'box1config1a.xyz', 'box2config1a.xyz']:
        job.add_output(f)
    if zeolite:
        job.add_input('zeolite.cif')
        job.add_output('zeolite.ztb')

def add(job, name, args):
    mcrun = '%s %s' % (MCRUN, args)
    postprocess = '%s %s %s' % (POST, name, job.dir)
    job.add_program(name, mcrun, True)
    job.add_program('post-%s' % name, postprocess, False)



class Setter:
    def set(self, job, parameters):
        raise NotImplementedError()

class MCSetter(Setter):
    def set(self, job, parameters):
        sim = Simulation(job.dir)
        for k, v in parameters.items():
            sim._set(k, v)
        sim.apply()