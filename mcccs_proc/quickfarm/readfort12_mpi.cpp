#include <iostream>
#include <mpi.h>
#include <string.h>
#include <fstream>
#include <sstream>
#include <vector>
#include <cstdio>

#define CALC_BOX1_VOL 0
#define MPI_SIZE_T MPI::UNSIGNED_LONG
#define MAX_LINE 1024

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

std::string read_file(std::string path, std::vector<std::string> suffix, int* nbox, int* nmoltype) {
    std::string line;
    
    // global properties and accumulators
    int iratp, ibox;
    int ncycle = 0;
    std::string buffer;
    double *boxvolume, *energy, *pressure;
    double **nmol;
    // variable of current line in file
    int idx_u;
    double v, u, p, n;
    *nbox = 0;
    for (int ifile = 0; ifile < suffix.size(); ifile++) {
        std::ifstream file(path + "/" + suffix[ifile]);
        if (file.is_open()) {
            // read header
            getline(file,line);

            // initialize accumulators
            ibox = 0;
            if (*nbox == 0) {
                std::istringstream headerStream(line);
                headerStream >> buffer >> iratp >> *nbox >> *nmoltype;
                boxvolume = new double[*nbox] {0};
                energy = new double[*nbox] {0};
                pressure = new double[*nbox] {0};
                nmol = new double*[*nbox] {0};
                for (int i = 0; i < *nbox; i++) {
                    nmol[i] = new double[*nmoltype] {0};
                }
            }
            while (getline(file,line)) {
                std::vector<std::string> tokens;
                tokens = split(line, ' ');
                idx_u = tokens.size() - *nmoltype - 2;
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
                for (int i = 0; i < *nmoltype; i++) {
                    n = stod(tokens[idx_u + 2 + i]);
                    nmol[ibox][i] += n;
                }
                // postprocess counters
                ibox++;
                if (ibox >= *nbox) {
                    ibox = 0;
                    ncycle++;
                }
            }
            file.close();
        }
    }

    std::string result;
    // convert sum to average
    if (ncycle > 0) {
        result = path + "," + std::to_string(ncycle);
        for (int i = 0; i < *nbox; i++) {
            boxvolume[i] /= ncycle;
            energy[i] /= ncycle;
            pressure[i] /= ncycle;
            result += "," + std::to_string(boxvolume[i]);
            result += "," + std::to_string(energy[i]);
            result += "," + std::to_string(pressure[i]);
            for (int j = 0; j < *nmoltype; j++) {
                nmol[i][j] /= ncycle;
                result += "," + std::to_string(nmol[i][j]);
            } 
        }
        result += "\n";
    } else {
    }
    return result;
}

int main(int argc, char* argv[]) {

    int num_procs, rank;
    std::string path, line;
    std::vector<std::string> suffix;
    MPI_Status status;

    /* argument indices are only correct after MPI_Init */
    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &num_procs);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    if (argc <= 1) {
        suffix.push_back("fort.12");
    } else {
        for (int i = 1; i < argc; i++) {
            std::string arg(argv[i]);
            std::cout << arg << "\n";
            suffix.push_back(arg + "/fort12." + arg);
        }
    }

    std::vector<std::string> paths, paths_rank, result;
    size_t *counts, *counts_sum, num_read, num_written;
    size_t count_rank, msglen;
    char* stringbuffer = new char[255];

    if (rank == 0) {
        std::ifstream file("runs.txt");
        if (file.is_open()) {
            while (getline(file, path)) {
                paths.push_back(path);
            }
            file.close();
        }
        counts = new size_t[num_procs];
        counts_sum = new size_t[num_procs];
        num_read = paths.size();
        /* Calculate number of files for each rank */
       
        for (int i = 0; i < num_procs; i++) {
            counts[i] = paths.size() / num_procs;
            if (i < paths.size() % num_procs) counts[i]++;
            counts_sum[i] = i == 0 ? 0 : counts_sum[i - 1] + counts[i - 1];
        }
    }
    MPI_Scatter(counts, 1, MPI_SIZE_T,
                &count_rank, 1, MPI_SIZE_T, 0, MPI_COMM_WORLD);
    /* Send path lists */
    if (rank == 0) {
        // Stores the root's jobs
        std::copy(paths.begin(), paths.begin() + counts[0], 
                std::back_inserter(paths_rank));
        // sends messages
        for (int t = 1; t < num_procs; t++) {
            for (int i = 0; i < counts[t]; i++) {
                msglen = paths[counts_sum[t] + i].length();
                MPI_Send(&msglen, 1, MPI_SIZE_T, t, i, MPI_COMM_WORLD);
                MPI_Send(paths[counts_sum[t] + i].c_str(), msglen, 
                    MPI::CHAR, t, counts[t] + i, MPI_COMM_WORLD);
            }
        }
    } else {
        for (int i = 0; i < count_rank; i++) {
            MPI_Recv(&msglen, 1, MPI_SIZE_T, 0, i, MPI_COMM_WORLD, &status);
            memset(stringbuffer, 0, sizeof(stringbuffer));
            MPI_Recv(stringbuffer, msglen, 
                    MPI::CHAR, 0, count_rank + i, MPI_COMM_WORLD, &status);
            std::string tempstr(stringbuffer, msglen);
            paths_rank.push_back(tempstr);
        }
    }
    std::cout << "Rank " << rank << " does " << paths_rank.size() << " entries \n";
    
    /* process files */
    int nbox, nmoltype;
    char* buffer = new char[MAX_LINE * count_rank];
    size_t ptr = 0;
    for (auto path : paths_rank) {
        line = read_file(path, suffix, &nbox, &nmoltype);
        line.copy(buffer + ptr, line.length(), 0);
        ptr += line.length();
    }
    /* output result */

    if (rank == 0) {
        std::ofstream outfile("fort12.csv");
        num_written = 0;
        if (outfile.is_open()) {
            line = csv_header(nbox, nmoltype);
            outfile << line;
            outfile.write(buffer, ptr);
            num_written += counts[0];
            for (int t = 1; t < num_procs; t++) {
                memset(buffer, 0, sizeof(buffer));
                MPI_Recv(&ptr, 1, MPI_SIZE_T, t, 2 * counts[t], MPI_COMM_WORLD, &status);
                MPI_Recv(buffer, ptr, 
                    MPI::CHAR, t, 2 * counts[t] + 1, MPI_COMM_WORLD, &status);
                num_written += counts[t];
                outfile.write(buffer, ptr);
            }
            std::cout << num_written << "/" << num_read << " files processed.\n";
            outfile.close();
        }
    } else {
        MPI_Send(&ptr, 1, MPI_SIZE_T, 0, 2 * count_rank, MPI_COMM_WORLD);
        MPI_Send(buffer, ptr, MPI::CHAR, 0, 2 * count_rank + 1, MPI_COMM_WORLD); 
    }

    MPI_Finalize();
    return 0;
}

