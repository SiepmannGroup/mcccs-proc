from subprocess import check_output
from preprocess import argparse_setup
RUN = '/home/andrewsun/MCCCS-MN/exe/src/topmon'

if __name__ == '__main__':
    argparse_setup('Run an MC Simulation')
    stdout = check_output([RUN]).decode('utf-8')
    if 'ERROR' in stdout:
        print("MCCCS-MN Error:")
        print(stdout)
        exit(1)
    else:
        print("Simulation finished successfully.")


