import sys, argparse
sys.path.append('/home/andrewsun/ssd0/simulations')
from random import randint
from mcccs_proc.simulation import Simulation

MAX_SEED = 1024
MIN_CUT = 14

kb = 1.38064852e-23
NA = 6.0221409e23

def equil(sim):
    sim.enable_displacement_change()
    sim.enable_pressure_calc(10)
    sim.set_allow_cutoff_failure(1)
    
def prod(sim):
    sim.disable_displacement_change()
    sim.enable_pressure_calc(5)
    sim.set_allow_cutoff_failure(1) #to prevent error exit for high-throughput runs

def setup(dir, nstep, seed, mode, time=0, vol='auto', swap=0.1, swatch=0, cbmc=0, rotation=3, rcut=0, other=None, keep_probs=False):
    sim = Simulation(dir)
    sim.set_cycle(nstep)
    sim.set_seed(seed)
    sim.set_time_limit(time)
    if mode == 'equil':
        equil(sim)
    elif mode == 'prod':
        prod(sim)
    else:
        raise ValueError("simulation mode should be 'equil' or 'prod'")
    if vol == 'auto':
        vol = sim.auto_v()
    if swap == 'auto':
        swap, cbmc, _ = sim.auto_s(dir)
    if rcut != 0:
        for i in range(1, sim.nbox()):
            new_cut = rcut * sum(sim.get_boxlength(i)) / 3
            if new_cut < MIN_CUT:
                print("Warning: specified cutoff ratio too small for box %d; reset to %d angstoms" % (i+1, MIN_CUT))
                new_cut = MIN_CUT
            sim.set_rcut(new_cut, i)
    if not sim.init:
        sim.flat_displacement()
    if other:
        for arg in other:
            key, value = arg.split('=')
            sim._set(key, value)
    if not keep_probs:
        sim.set_move_probs(n_rot=rotation, vprob=vol, sprob=swap, iprob=swatch, cprob=cbmc)
    sim.apply()

def initialize_2box(dir, temperature, pressure, n_init, rholiquid):
    BOXMIN = 40
    BOXLMIN = 32
    NGMIN = 200
    sim = Simulation(dir)
    sim.set_temperature(temperature)
    sim.set_pressure(pressure)
    # initialize as liquid if rholiquid (mol/L) > 0, assuming fixed density
    if rholiquid > 0:
        # 1 ang = 1e-10 m = 1e-9 dm
        n_init_l = int((BOXLMIN / 1e9) ** 3 * rholiquid * NA) + n_init - NGMIN
        # if the liquid box contains less than n_init molecules, still use n_init
        n_init = max(n_init_l, n_init)
        init_boxl = (n_init / NA / rholiquid) ** (1/3) * 1e9
        # relax box length by 3 ang to prevent configuration overlap
        init_boxl += 3
    else:
        init_boxl = max(BOXMIN, (n_init * kb * temperature / pressure) ** (1/3) * 1e8)
    sim.set_boxlength(init_boxl, 1)
    sim.set_init_config(n_init, 1)
    sim._set("nchain", str(n_init))
    sim._set("rmvolume", "%.5e" % (0.1 * (init_boxl ** 3)))
    sim.apply()

def initialize_2box_binary(dir, temperature, pressure, n_init_each, rholiquid, is_cbmc):
    BOXMIN = 40
    BOXLMIN = 32
    NGMIN = 200
    n_init = sum(n_init_each)
    sim = Simulation(dir)
    sim.set_temperature(temperature)
    sim.set_pressure(pressure)
    # initialize as liquid if rholiquid (mol/L) > 0, assuming fixed density
    if rholiquid > 0:
        # 1 ang = 1e-10 m = 1e-9 dm
        n_init_l = int((BOXLMIN / 1e9) ** 3 * rholiquid * NA) + n_init - NGMIN
        # if the liquid box contains less than n_init molecules, still use n_init
        if n_init_l > n_init:
            fac = n_init_l / n_init
            for i in range(len(n_init_each)):
                n_init_each[i] = int(round(n_init_each[i] * fac))
        n_init = sum(n_init_each)
        init_boxl = (n_init / NA / rholiquid) ** (1/3) * 1e9
        # relax box length by 10 angstroms to prevent configuration overlap
        init_boxl += 10
    else:
        init_boxl = max(BOXMIN, (n_init * kb * temperature / pressure) ** (1/3) * 1e8)
    sim.set_boxlength(init_boxl, 1)
    sim.set_init_config(n_init_each, 1)
    sim._set("nchain", str(n_init))
    sim._set("rmvolume", "%.5e" % (0.1 * (init_boxl ** 3)))
    if is_cbmc[0] and is_cbmc[1]:
        sim._set("pmcbmt", ["%.5f" % (n_init_each[0] / n_init), "1.0"])
    elif is_cbmc[0] and not(is_cbmc[1]):
        sim._set("pmcbmt", ["1.0", "1.0"])
    elif not is_cbmc[0] and is_cbmc[1]:
        sim._set("pmcbmt", ["0.0", "1.0"])
    else:
        sim._set("pmcbmt", ["0.0", "0.0"])
    sim._set("pmtrmt", ["%.5f" % (n_init_each[0] / n_init), "1.0"])
    sim._set("pmromt", ["%.5f" % (n_init_each[0] / n_init), "1.0"])
    sim._set("pmswmt", ["%.5f" % (n_init_each[0] / n_init), "1.0"])
    sim.apply()

def parse_args(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('mode', help='simulation mode', type=str)
    parser.add_argument('nstep', help='number of cycles', type=int)
    parser.add_argument('-x', '--seed', help='random seed', type=int, default=randint(0, MAX_SEED))
    parser.add_argument('-t', '--time', help='time limit of simulation', type=int, default=0)
    parser.add_argument('-p', '--path', help='path to input files', type=str, default='.')
    parser.add_argument('-v', '--volume', help='volume move probability', type=float, default=2)
    parser.add_argument('-s', '--swap', help='swap move probability', type=float, default=2)
    parser.add_argument('-i', '--swatch', help='swatch move probability', type=float, default=0)
    parser.add_argument('-c', '--cbmc', help='CBMC move probability', type=float, default=0)
    parser.add_argument('-r', '--rotation', help='number of rotation DOF', type=int, default=3)
    parser.add_argument('-rc', '--rcut', help='cutoff ratio of vapor boxes', type=float, default=0)
    parser.add_argument('-o', '--other', help='other input parameters to change', type=str, nargs='*')
    parser.add_argument('-k', '--keep', help='keep move probabilities', action='store_true')
    args = vars(parser.parse_args())
    pvol = 'auto' if args['volume'] == 2 else args['volume']
    pswap = args['swap']
    if args['mode'] == 'equil' and args['swap'] == 2:
        pswap = 0.1
    if args['mode'] == 'prod' and args['swap'] == 2:
        pswap = 'auto'
    args['volume'] = pvol
    args['swap'] = pswap
    return args

def argparse_setup(description):
    args = parse_args(description)
    setup(args['path'], args['nstep'], args['seed'], args['mode'], time=args['time'], \
            vol=args['volume'], swap=args['swap'], swatch=args['swatch'], cbmc=args['cbmc'], 
            rotation=args['rotation'], rcut=args['rcut'], other=args['other'], keep_probs=args['keep'])
    #initialize_2box(args['path'], 77, 3, 1250)
    


if __name__ == '__main__':
    argparse_setup('set up MC simulation')
    
    

    
