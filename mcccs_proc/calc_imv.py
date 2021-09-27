import subprocess, sys, os

def tail(file, nline):
    lines = subprocess.check_output(["tail", "-n", str(nline), file]).decode('utf-8').strip().split('\n')
    return lines

BASE_SIZE = 350
TARGET_FRAME_SIZE = 1000

def calc_imv(path, nbox=2, ncycle=100):
    lines = tail(path, ncycle * nbox)
    nzeo = [int(line.split()[-1]) for i, line in enumerate(lines) if i % nbox == 0]
    nzeo_avg = sum(nzeo) / ncycle
    if nzeo_avg < 1 / ncycle:
        return 200000
    frame_size = nzeo_avg * BASE_SIZE
    imv = max(1, round(frame_size / TARGET_FRAME_SIZE))
    #print("frame size:", frame_size, "target size", TARGET_FRAME_SIZE)
    return imv

if __name__ == "__main__":
    print(calc_imv(sys.argv[1]))
