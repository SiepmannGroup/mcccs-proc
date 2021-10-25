#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <cstdio>

#define CALC_BOX1_VOL 0

std::vector<std::string> split(const std::string& s, char delimiter) {
    std::vector<std::string> tokens;
    std::istringstream tokenStream(s);
    for (std::string token; tokenStream >> token;) {
        tokens.push_back(token);
    }
    return tokens;
}

std::string csv_header(int nbox, int nmoltype) {
    std::string line;
    line += "Path,Cycles";
    for (int i = 0; i < nbox; i++) {
        line += ",Box " + std::to_string(i) +  " volume";
        line += ",Box " + std::to_string(i) +  " energy";
        line += ",Box " + std::to_string(i) +  " pressure";
        for (int j = 0; j < nmoltype; j++) {
            line += ",Box " + std::to_string(i) +  " mol " + std::to_string(j);
        }
    }
    line += "\n";
    return line;
}

std::string read_file(std::string path) {
    std::string line;
    std::ifstream file(path + "/fort.12");
    // global properties and accumulators
    int iratp, ibox, nbox, nmoltype;
    int ncycle = 0;
    std::string buffer;
    double *boxvolume, *energy, *pressure;
    double **nmol;
    // variable of current line in file
    int idx_u;
    double v, u, p, n;

    if (file.is_open()) {
        // read header
        getline(file,line);
        std::istringstream headerStream(line);
        headerStream >> buffer >> iratp >> nbox >> nmoltype;

        // initialize accumulators
        ibox = 0;
        boxvolume = new double[nbox] {0};
        energy = new double[nbox] {0};
        pressure = new double[nbox] {0};
        nmol = new double*[nbox] {0};
        for (int i = 0; i < nbox; i++) {
            nmol[i] = new double[nmoltype] {0};
        }

        while (getline(file,line)) {
            std::vector<std::string> tokens;
            tokens = split(line, ' ');
            idx_u = tokens.size() - nmoltype - 2;
            // only calculates volume for orthorombic cell 
            if ((ibox > 0 || CALC_BOX1_VOL) && idx_u == 3) {
                v = stod(tokens[0]) * stod(tokens[1]) * stod(tokens[2]);
            } else {
                v = 0;
            }
            u = stod(tokens[idx_u]);
            // only calculates pressure at iratp cycles 
            if ((ncycle + 1) % iratp == 0) {
                p = stod(tokens[idx_u + 1]);
                pressure[ibox] += p;
            }
            boxvolume[ibox] += v;
            energy[ibox] += u;
            for (int i = 0; i < nmoltype; i++) {
                n = stod(tokens[idx_u + 2 + i]);
                nmol[ibox][i] += n;
            }
            // postprocess counters
            ibox++;
            if (ibox >= nbox) {
                ibox = 0;
                ncycle++;
            }
        }
        file.close();
    }

    std::string result;
    // convert sum to average
    if (ncycle > 0) {
        result = path + "," + std::to_string(ncycle);
        for (int i = 0; i < nbox; i++) {
            boxvolume[i] /= ncycle;
            energy[i] /= ncycle;
            pressure[i] /= ncycle;
            result += "," + std::to_string(boxvolume[i]);
            result += "," + std::to_string(energy[i]);
            result += "," + std::to_string(pressure[i]);
            for (int j = 0; j < nmoltype; j++) {
                nmol[i][j] /= ncycle;
                result += "," + std::to_string(nmol[i][j]);
            } 
        }
        result += "\n";
    }
    return result;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cout << "Usage: readfort12 nbox nmoltype\n";
        exit(1); 
    }
    std::ifstream file("runs.txt");
    std::string path;
    std::string line;
    int nbox, nmoltype;
    nbox = atoi(argv[1]);
    nmoltype = atoi(argv[2]);
    if (file.is_open()) {
        std::ofstream outfile("fort12.csv");
        if (outfile.is_open()) {
            line = csv_header(nbox, nmoltype);
            outfile << line;
            while (getline(file, path)) {
                line = read_file(path);
                outfile << line;
            }
            outfile.close();
        }
        file.close();
    }
}

