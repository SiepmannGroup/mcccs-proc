import os
from subprocess import check_output
from mcccs_proc.utils import read_inp_restart, toint, tofloat, clean, avg_displacement
from mcccs_proc.file_io import write_fort4, write_restart

class Simulation:
    box_props = ['dimensions', 'rcut', 'temperature', 'pressure']

    def __init__(self, dir, f_in='fort.4', f_restart='fort.77'):
        self.f_in = os.path.join(dir, f_in)
        self.f_restart = os.path.join(dir, f_restart)
        self.in_data, self.restart_data = read_inp_restart(self.f_in, self.f_restart)
        if self.restart_data is None:
            self.init = True
            self._set('linit', 'T')
        else:
            self.init = False
            self._set('linit', 'F')


    # generic setter and getter method
    # value should be already formatted as string
    def _set(self, key, value):
        if type(value) != list:
            value = str(value)
        if key in Simulation.box_props:
            items = self.in_data['SIMULATION_BOX'].items()
        else:
            items = self.in_data.items()
        found = False
        for _, section in items:
            if key in section:
                if type(section[key]) != dict:
                    section[key] = value
                else:
                    section[key] = {f"mol{i+1}": value[i] for i in range(len(value))}
                found = True
        if not found:
            raise KeyError('key %s not included in input file!' % key)
        return self

    def _add(self, section, key, value):
        if section not in self.in_data:
            self.in_data[section] = {}
        self.in_data[section][key] = value
        return self

    def _get(self, key):
        get = []
        if key in Simulation.box_props:
            items = self.in_data['SIMULATION_BOX'].items()
        else:
            items = self.in_data.items()
        for _, section in items:
            if key in section:
                get.append(section[key])
        if not get:
            return None
        elif len(get) == 1:
            return get[0]
        else:
            return get

    def _del(self, key):
        for _, section in self.in_data.items():
            if key in section:
                section.pop(key)
        return self

    def nbox(self):
        return len(self.in_data['SIMULATION_BOX'].keys())

    def set_seed(self, seed):
        return self._set('seed', "%d" % seed)

    def set_cycle(self, cycle):
        return self._set('nstep', "%d" % cycle)

    def set_time_limit(self, t):
        if t <= 0:
            return self.disable_time_limit()
        return self._add('&mc_shared', 'time_limit', "%i" % t)

    def disable_time_limit(self):
        return self._del('time_limit')
    
    def get_cycle(self):
        return toint(self._get('nstep'))

    def set_boxlength(self, boxl, i):
        if self._get("linit").strip() != 'T':
            raise ValueError("Can directly set box length only when initialization!")
        self.in_data['SIMULATION_BOX']['box%d' % (i + 1)]['dimensions'] = ' '.join(["%.3f"%boxl] * 3)
        if boxl < 40:
            self.set_rcut(14, i)
        else:
            self.set_rcut(0.35 * boxl, i)

    def get_boxlength(self, i):
        if self.restart_data:
            raw = self.restart_data['box dimensions']['box%d' % (i + 1)]
        else:
            raw = self.in_data['SIMULATION_BOX']['box%d' % (i + 1)]['dimensions']
        return [float(x) for x in raw.split()]

    def set_rcut(self, rcut, i):
        v = self.in_data['SIMULATION_BOX']['box%d' % (i + 1)]
        v['rcut'] = "%.5f" % rcut
        return self

    def get_rcut(self):
        rcut = {}
        for k, v in self.in_data['SIMULATION_BOX'].items():
            rcut[k] = tofloat(v['rcut'])
        return rcut

    def set_temperature(self, temp):
        for _, v in self.in_data['SIMULATION_BOX'].items():
            v['temperature'] = "%.5f" % temp
        return self

    # pressure unit: MPa
    def set_pressure(self, pres):
        for _, v in self.in_data['SIMULATION_BOX'].items():
            v['pressure'] = "%.5f" % pres
        return self

    def set_init_config(self, ninit, i):
        if type(ninit) != int:
            ninit_each = ninit
            ninit = sum(ninit)
        else:
            ninit_each = [ninit]
        n_initgrid = [int(ninit ** (1/3))] * 3
        n_initgrid[0] += 1
        if (n_initgrid[0] * n_initgrid[1] * n_initgrid[2]) < ninit:
            n_initgrid[1] += 1
        if (n_initgrid[0] * n_initgrid[1] * n_initgrid[2]) < ninit:
            n_initgrid[2] += 1
        if (n_initgrid[0] * n_initgrid[1] * n_initgrid[2]) < ninit:
            raise ValueError("Error in initial structure: total %s, grid %s" % (ninit, ninitgrid))
        dshift = self.get_boxlength(i)[0] / n_initgrid[0] / 2
        init_line = self.in_data['SIMULATION_BOX']['box%d' % (i + 1)]["initialization data"].split()
        for j in range(3):
            init_line[j] = str(n_initgrid[j])
        init_line[5] = "%.3f" % dshift
        self.in_data['SIMULATION_BOX']['box%d' % (i + 1)]["initialization data"] = " ".join(init_line)
        for imol in range(len(ninit_each)):
            self.in_data['SIMULATION_BOX']['box%d' % (i + 1)]["mol%i" % (imol + 1)] = str(ninit_each[imol])
    
    def set_allow_cutoff_failure(self, val):
        self.in_data['&mc_volume']['allow_cutoff_failure'] = "%i" % val
        return self

    def enable_displacement_change(self, interval=250):
        if interval <= 0:
            return self.disable_displacement_change()
        self.in_data['&mc_shared']['iratio'] = "%i" % interval
        self.in_data['&mc_volume']['iratv'] = "%i" % interval
        return self
    
    def disable_displacement_change(self):
        self.in_data['&mc_shared']['iratio'] = "%i" % (self.get_cycle() + 100)
        self.in_data['&mc_volume']['iratv'] = "%i" % (self.get_cycle() + 100)
        return self

    def enable_pressure_calc(self, interval=10):
        if interval <= 0:
            return self.disable_pressure_calc()
        self.in_data['&analysis']['iratp'] = "%i" % interval
        return self
    
    def disable_pressure_calc(self):
        self.in_data['&analysis']['iratp'] = "%i" % (self.get_cycle() + 100)
        return self

    # complex modifications
    def flat_displacement(self):
        if self.init:
            print("Simulation does not have checkpoint file, skipped changing max displacement")
            return self
        rcut = self.get_rcut()
        # always average maximum displacement
        for box, value in self.restart_data['max displacement']['translation'].items():
            for mol, line in value.items():
                self.restart_data['max displacement']['translation'][box][mol] \
                        = avg_displacement(line, 2*rcut[box]) + '\n'
        return self

    # MC Moves
    # naming conventions as [a-z]move, [a-z]prob
    # v: volume; s: swap; i: swatch (identity switch)
    # c: cbmc; t: translation; r: rotation

    def set_prob(self, code, p):
        if code == 'v':
            if '&mc_volume' in self.in_data:
                self.in_data['&mc_volume']['pmvol'] = '%.5f' % p
        elif code == 'i':
            if '&mc_swatch' in self.in_data:
                self.in_data['&mc_swatch']['pmswat'] = '%.5f' % p
        elif code == 's':
            if '&mc_swap' in self.in_data:
                self.in_data['&mc_swap']['pmswap'] = "%.5f" % p
        elif code == 'c':
            if '&mc_cbmc' in self.in_data:
                self.in_data['&mc_cbmc']['pmcb'] = "%.5f" % p
                #self.in_data['&mc_cbmc']['pmcbmt'] = "1.0"
        elif code == 't':
            if '&mc_simple' in self.in_data:
                self.in_data['&mc_simple']['pmtra'] = "%.5f" % p
        else:
            raise ValueError('Invalid MC move type!')

    def get_prob(self, code):
        p = -1
        if code == 'v':
            if '&mc_volume' in self.in_data:
                p = self.in_data['&mc_volume']['pmvol']
        elif code == 'i':
            if '&mc_swatch' in self.in_data:
                p = self.in_data['&mc_swatch']['pmswat']
        elif code == 's':
            if '&mc_swap' in self.in_data:
                p = self.in_data['&mc_swap']['pmswap']
        elif code == 'c':
            if '&mc_cbmc' in self.in_data:
                p = self.in_data['&mc_cbmc']['pmcb']
        elif code == 't':
            if '&mc_simple' in self.in_data:
                p = self.in_data['&mc_simple']['pmtra']
        else:
            raise ValueError('Invalid MC move type!')
        return tofloat(p)


    # automatic move probabilities
    # n_rot:rotational degrees of freedom
    def set_move_probs(self, n_rot=3, vprob=-1, sprob=-1, iprob=-1, cprob=-1):
        # clear all probabilities
        for c in ['v', 'i', 's', 'c', 't']:
            self.set_prob(c, -1)
        prob_sum = 0
        for c, p in zip(['v', 'i', 's', 'c'], [vprob, iprob, sprob, cprob]):
            if p > 0:
                prob_sum += p
                self.set_prob(c, prob_sum)
        tprob = (1 - prob_sum) * 3 / (3 + n_rot)
        self.set_prob('t', prob_sum + tprob)

    def auto_v(self):
        nmol = int(self.in_data['&mc_shared']['nchain'])
        tavol = float(self.in_data['&mc_volume']['tavol'].strip().rstrip('d0'))
        return 0.1 / nmol / tavol

    # need the working directory to calculate swap acceptance
    def auto_s(self, dir):
        SCR = '/home/asunumn/scripts/mcccs_proc/adjustswap_nosum.sh'
        res = check_output(['bash', SCR, dir])
        out = [float(x) for x in res.decode('utf-8').strip().split()]
        #print(res, out)
        return out[0], out[1], out[2]

    def scale_swap_prob(self, scale):
        # p{swap,..} denote individual probability
        pswatch = self.get_prob('i') - self.get_prob('v')
        if pswatch < 1e-5:
            pswatch = 0
        pswap = self.get_prob('s') - max(self.get_prob('i'), self.get_prob('v'))
        if (pswatch + pswap) * scale > 0.5:
            scale = 0.5 / (pswatch + pswap) 
        # {swap,..} denote cumulative probability
        swatch = self.get_prob('v') + scale * pswatch
        swap = swatch + scale * pswap
        pcbmc = self.get_prob('c') - self.get_prob('s')
        ptrans = self.get_prob('t') - self.get_prob('c')
        prot = 1 - self.get_prob('t')
        wtot = pcbmc + ptrans + prot
        wcbmc, wtrans, wrot = pcbmc/wtot, ptrans/wtot, prot/wtot
        wnew = 1 - swap
        if pswatch > 0:
            self.set_prob('i', swatch)
        self.set_prob('s', swap)
        self.set_prob('c', swap + wcbmc * wnew)
        self.set_prob('t', swap + (wcbmc + wtrans) * wnew)


    # file IO
    def apply(self):
        clean(self.in_data)
        write_fort4(self.in_data, self.f_in)
        if not self.init:
            write_restart(self.restart_data, self.f_restart)


    
