
import sys
sys.path.append('/home/andrewsun/ssd0/simulations')
from MCFlow.file_formatting import reader
from MCFlow.file_formatting import writer
import os, argparse
import numpy as np

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='make files for P/T w/in zeolite')
    parser.add_argument('-r','--restart',help='restart file',type=str)
    parser.add_argument('-f','--input',help='input file (fort.4)',type=str)
    args = vars(parser.parse_args())
    input_data = reader.read_fort4(args['input'])
    nmolty = int(input_data['&mc_shared']['nmolty'])
    restart_data = reader.read_restart(args['restart'],
                                       nmolty,
                                       int(input_data['&mc_shared']['nbox']))
    print(input_data)
    print(restart_data.keys())
    print(restart_data['box dimensions']['box1'].split())
    writer.write_restart(restart_data, 'fort.77.new')
    writer.write_fort4(input_data, 'fort.4.new')
