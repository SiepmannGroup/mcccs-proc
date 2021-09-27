import subprocess, sys, os
import pandas as pd

def grep(file, string):
    lines = subprocess.check_output(["grep", string, file]).decode('utf-8').strip().split('\n')
    return lines

# keys_row should all preceed keys_col
def get_values(file, nbox, keys_row, keys_col):
    hit = grep(file, "\|".join(keys_row + keys_col))
    lines_row = hit[:len(keys_row)]
    lines_col = hit[len(keys_row) * nbox:]
    if len(lines_col) != len(keys_col):
        raise ValueError("Inconsistent number of matches!")
    data = [os.path.dirname(file)]
    for l in lines_row:
        data.append(l.split()[-2])
    for l in lines_col:
        data.extend(l.split()[-2:])
    return data

def scrape_data(files, nbox, keys_row, keys_col):
    names = ['path'] + [x.strip() for x in keys_row] + [x.strip() + " box %d" % i for x in keys_col for i in range(1, nbox + 1)]
    data_all = []
    for f in files:
        data_all.append(get_values(f, nbox, keys_row, keys_col))
    df = pd.DataFrame(data_all, columns=names)
    return df
nbox = 2

keys_row = ["  temperature",
        "external pressure",]
keys_col = ["chem. potential ",
        "no. of chains ",
        "specific density            "]

if len(sys.argv) > 1:
    df = scrape_data(sys.argv[1:], nbox, keys_row, keys_col)
    df.to_csv('run1a.csv')
else:
    print("No file supplied, exit.")