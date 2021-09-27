#file IO from MCFlow
def read_fort4(file):
    input_data = {}
    f = open(file)
    nmolty = -1
    nbox = -1
    for line in f:
        if len(line.split()) == 0:
            continue
        elif line.split()[0].startswith('&'):
            # in namelist section
            namelist = line.split()[0]
            input_data[namelist] = {}
        elif line.split()[0].startswith('/'):
            namelist = ''
        elif namelist:
            variable = line.split()[0]
            if '=' == variable[-1]: variable = variable.rstrip('=')
            values = line[(line.find('=')+1):]
            my_val = 'None'
            if (variable == 'pmsatc'):
                my_val = {'swatch%i'%i:values.split()[i-1]
                          for i in range(1, len(values.split())+1)}
            elif variable == 'pmswmt':
                my_val = {'mol%i'%i:values.split()[i-1] for i in range(1,nmolty+1)}
            elif (len(values.split()) == 1) and (variable != 'pmvlmt'):
                my_val = values.rstrip('\n')
                if variable == 'nmolty':
                    nmolty = int(values)
                elif variable == 'nbox':
                    nbox = int(values)
            elif (variable  == 'pmvlmt'):
                my_val = {'box%i'%i:values.split()[i-1] for i in range(1,nbox+1)}
            elif len(values.split()) == nmolty:
                my_val = {'mol%i'%i:values.split()[i-1] for i in range(1,nmolty+1)}
            elif len(values.split()) == nbox:
                my_val = {'box%i'%i:values.split()[i-1] for i in range(1,nbox+1)}
            elif len(values.split()) > nbox and len(values.split()) < nmolty:
                my_val = {'box%i'%i:values.split()[i-1] for i in range(1,nbox+1)}
            elif len(values.split()) > nmolty:
                my_val = {'box%i'%i:values.split()[i-1] for i in range(1,nbox+1)}
            else:
                print('error in input file for variable',variable)
                # there was an error in previous input file
                if variable == 'pmswmt':
                    print('there were too many swap types in pmswmt')
                    my_val = {'mol%i'%i:values.split()[i-1] for i in range(1,nmolty+1)}
            input_data[namelist][variable] = my_val
        elif (len(line.split()) == 1) and line.split()[0].isupper():
            section = line.split()[0]
            itype = 0
            input_data[section] = {}
        elif line.split()[0] == 'END':
            section = ''
        elif section == 'SIMULATION_BOX':
            while ((itype != nbox) or (not line.split())):
                if 'box%i'%(itype+1) not in input_data[section].keys():
                    input_data[section]['box%i'%(itype+1)] = {}
                line = next(f)
                if 'END' in line:
                    print(itype, input_data[section])
                if not line.startswith('!'):
                    if (len(line.split()) == 13) and ('F' in line):
                        (boxlx, boxly, boxlz, rcut, kalp, rcutnn,
                        NDII, lsolid, lrect, lideal, ltwice, T, P) = line.split()
                        input_data[section]['box%i'%(itype+1)]['dimensions'] = '%s %s %s'%(boxlx, boxly, boxlz)
                        input_data[section]['box%i'%(itype+1)]['rcut'] = rcut
                        input_data[section]['box%i'%(itype+1)]['defaults'] = '{} {} {} {} {} {} {}'.format(kalp, rcutnn, NDII,
                                                                                        lsolid, lrect,lideal, ltwice)
                        input_data[section]['box%i'%(itype+1)]['temperature'] = T
                        input_data[section]['box%i'%(itype+1)]['pressure'] = P
                    elif (len(line.split()) == 9) and ('F' in line):
                        input_data[section]['box%i'%(itype+1)]['initialization data'] = line
                        itype += 1
                    elif len(line.split()) == nmolty + 1:
                        nmols = line.split()[:-1]
                        nghost = line.split()[-1]
                        for i in range(1,len(nmols)+1):
                            input_data[section]['box%i'%(itype+1)]['mol%i'%i] = nmols[i-1]
                        input_data[section]['box%i'%(itype+1)]['nghost'] = nghost
                    elif len(line.split()) == nmolty + 2:
                        nmols = line.split()[:-2]
                        nghost = line.split()[-2]
                        for i in range(1,len(nmols)+1):
                            input_data[section]['box%i'%(itype+1)]['mol%i'%i] = nmols[i-1]
                        input_data[section]['box%i'%(itype+1)]['nghost'] = nghost
        elif section == 'MOLECULE_TYPE':
            if 'nunit' in line:
                itype += 1
                input_data[section]['mol%i'%itype] = ''
            if line.split() and itype > 0:
                input_data[section]['mol%i'%itype] += line
        elif section == 'MC_SWAP':
            if line.split() and line[0].isdigit():
                if len([i for i in line.split() if i.isdigit()]) == 2:
                    # line is box1, box2
                    swap_pair += 1
                    input_data[section]['mol%i'%itype]['box1 box2'][swap_pair] = list(map(int,line.split()))
                else:
                    itype += 1
                    input_data[section]['mol%i'%itype] = {'nswapb':0,'pmswapb':[]}
                    nswapb = int(line.split()[0])
                    input_data[section]['mol%i'%itype]['nswapb'] = nswapb
                    input_data[section]['mol%i'%itype]['pmswapb'] = list(map(float, [i.rstrip('d0') for i in line.split()[1:]]))
                    input_data[section]['mol%i'%itype]['box1 box2'] = [0 for i in range(nswapb)]
                    swap_pair = -1
        elif section == 'MC_SWATCH':
            if 'moltyp1<->moltyp2' in line:
                itype += 1
                input_data[section]['swatch%i'%itype] = ''
            if (itype > 0) and line.split():
                input_data[section]['swatch%i'%itype] += line
        elif section == 'INTERMOLECULAR_EXCLUSION':
            if (line.rstrip('\n').replace(' ','').isdigit()):
                mol1, unit1, mol2, unit2 = map(int,line.split())
                if 'mol%i'%mol1 not in input_data[section].keys():
                    input_data[section]['mol%i'%mol1] = {}
                if 'unit%i'%unit1 not in input_data[section]['mol%i'%mol1].keys():
                    input_data[section]['mol%i'%mol1]['unit%i'%unit1] = {}
                if 'mol%i'%mol2 not in input_data[section]['mol%i'%mol1]['unit%i'%unit1].keys():
                    input_data[section]['mol%i'%mol1]['unit%i'%unit1]['mol%i'%mol2] = []
                input_data[section]['mol%i'%mol1]['unit%i'%unit1]['mol%i'%mol2].append( 'unit%i'%unit2 )
        elif section == 'INTRAMOLECULAR_OH15':
            if (line.rstrip('\n').replace(' ','').isdigit()):
                mol = int(line.split()[0])
                if 'mol%i'%mol not in input_data[section].keys():
                    input_data[section]['mol%i'%mol] = []
                input_data[section]['mol%i'%mol] += [line[line.find(' '):]]
        elif section == 'INTRAMOLECULAR_SPECIAL':
            params = line.split()
            if params[0].isdigit():
                mol, i, j, logic, sLJ, sQ = list(map(int,params[:4])) +  list(map(float,params[-2:]))
                if 'mol%i'%mol not in input_data[section].keys():
                    input_data[section]['mol%i'%mol] = []
                input_data[section]['mol%i'%mol].append( '%i %i %i %2.1f %2.1f'%(i,j,logic,sLJ, sQ))
        elif section == 'UNIFORM_BIASING_POTENTIALS':
            if '!' not in line:
                itype += 1
                mol = 'mol%i'%itype
                if mol not in input_data[section].keys():
                    input_data[section][mol] = {}
                for i in range(len(line.split())):
                    my_box = 'box%i'%(i+1)
                    if my_box not in input_data[section][mol].keys():
                        input_data[section][mol][my_box] = {}
                    new_var = line.split()[i]
                    if 'd0' in new_var: new_var = new_var.rstrip('d0')
                    input_data[section][mol][my_box] = float(new_var)
        else:
            print( section, 'is missing formatting')
    return input_data

def read_restart(file, nmolty, nbox):
    config_data = {'max displacement':{}}
    moltyp = 0
    ibox = 0
    charge_moves = []
    nunit = []
    mol_types = []
    box_types = []
    f = open(file)
    nline = 0
    for line in f:
        nline += 1
        if 'number of cycles' not in config_data.keys():
            config_data['number of cycles'] = line
        elif 'atom translation' not in config_data['max displacement'].keys():
            config_data['max displacement']['atom translation'] = line
        elif (moltyp != nmolty) and (ibox != nbox):
            for ibox in range(1,nbox+1):
                for moltyp in range(1, nmolty+1):
                    if 'translation' not in config_data['max displacement'].keys():
                        # first time
                        config_data['max displacement']['translation'] = {'box%i'%i:{'mol%i'%j:''
                                                                                     for j in range(1, nmolty+1)}
                                                                          for i in range(1, nbox+1)}
                        config_data['max displacement']['rotation'] = {'box%i'%i:{'mol%i'%j:''
                                                                                     for j in range(1, nmolty+1)}
                                                                          for i in range(1, nbox+1)}
                        config_data['max displacement']['translation']['box%i'%ibox]['mol%i'%moltyp] = line
                        config_data['max displacement']['rotation']['box%i'%ibox]['mol%i'%moltyp] = next(f)
                    elif not config_data['max displacement']['translation']['box%i'%ibox]['mol%i'%moltyp]:
                        config_data['max displacement']['translation']['box%i'%ibox]['mol%i'%moltyp] = next(f)
                        config_data['max displacement']['rotation']['box%i'%ibox]['mol%i'%moltyp] = next(f)
        elif len(charge_moves) < nbox*nmolty:
            if 'fluctuating charge' not in config_data['max displacement'].keys():
                config_data['max displacement']['fluctuating charge'] = {'box%i'%i:{'mol%i'%j:''
                                                                                     for j in range(1, nmolty+1)}
                                                                          for i in range(1, nbox+1)}
            charge_moves = charge_moves + line.split()
            if len(charge_moves) == nbox*nmolty:
                for i in range(len(charge_moves)):
                    c_box = i // nmolty + 1
                    c_mol = i % nmolty + 1
                    config_data['max displacement']['fluctuating charge']['box%i'%c_box]['mol%i'%c_mol] = charge_moves[i]
            elif len(charge_moves) > nbox*nmolty:
                print('error reading max displ for translation and rotation')
                print(config_data['max displacement'])
                print(nline)
                quit()
        elif 'volume' not in config_data['max displacement'].keys():
            config_data['max displacement']['volume'] = {}
            for index, value in enumerate(line.split()):
                config_data['max displacement']['volume']['box%i'%(index+1)] = value
            if len(config_data['max displacement']['volume'].keys()) != nbox:
                line = next(f)
                cbox = len(config_data['max displacement']['volume'].keys())
                for index, value in enumerate(line.split()):
                    config_data['max displacement']['volume']['box%i'%(cbox + index+1)] = value
        elif 'box dimensions' not in config_data.keys():
            if (len(line.split()) == 9):
                config_data['box dimensions']={'box1': next(f) }
            else:
                config_data['box dimensions']={'box1': line }
            for i in range(2,nbox+1):
                config_data['box dimensions']['box%i'%i] = next(f)
        elif 'nchain' not in config_data.keys():
            if len(line.split()) == 3:
                box_info  = ''
                missing_lines = 5
                for key, value in config_data['box dimensions'].items():
                    box_info += value
                for i in range(missing_lines):
                    box_info += line
                    line = next(f)
                config_data['box dimensions'] = {'box%i'%i:'' for i in range(1, nbox+1)}
                for c, box_d in enumerate(box_info.split('\n')):
                    if box_d:
                        ibox = c + 1 - missing_lines
                        if ibox < 1: ibox = 1
                        config_data['box dimensions']['box%i'%ibox] += box_d + '\n'
            config_data['nchain'] = line
            nchain = int(line.split()[0])
        elif 'nmolty' not in config_data.keys():
            config_data['nmolty'] = line
            nmolty = int(line.split()[0])
        elif len(nunit) < nmolty:
            nunit += line.split()
            if 'nunit' not in config_data.keys(): config_data['nunit'] = {}
            if len(nunit) == nmolty:
                for i in range(1,len(nunit)+1):
                    config_data['nunit']['mol%i'%i] = nunit[i-1]
        elif len(mol_types) < nchain:
            mol_types += line.split()
            if len(mol_types) == nchain:
                config_data['mol types'] = mol_types
        elif len(box_types) < nchain:
            box_types += line.split()
            if len(box_types) == nchain:
                config_data['box types'] = box_types
        else:
            config_data['coords'] = []
            icoords = ''
            for mol_number in config_data['mol types']:
                nbead_mol = int(config_data['nunit']['mol%s'%mol_number])
                molecule_coords = []
                for bead in range(1, nbead_mol+1):
                    if icoords == '':
                        icoords = line
                    else:
                        icoords= next(f)
                    if len(icoords.split()) == 4:
                        q = icoords.split()[3] + '\n'
                        xyz = ' '.join(icoords.split()[:3]) + ' '
                    else:
                        xyz = icoords
                        q = next(f)
                    molecule_coords.append({'xyz':xyz,'q':q})
                config_data['coords'].append(molecule_coords)
    return config_data


def write_fort4(data, newfile):
    indent = ' '*4
    f = open(newfile,'w')
    namelists = [i for i in data.keys() if i.startswith('&')]
    sections = [i for i in data.keys() if i not in namelists]
    variable_order = {'&mc_shared':('seed','nbox','nmolty','nchain','nstep', 'time_limit',
                                    'iratio','rmin','softcut','linit','lreadq'),
                      '&analysis':('iprint','imv','iblock','iratp','idele',
                                    'iheatcapacity','ianalyze'),
                      '&mc_volume':('tavol','iratv','pmvlmt','nvolb','pmvolb',
                                    'pmvol','pmvolx','pmvoly','rmvolume',
                                    'allow_cutoff_failure'),
                      '&mc_swatch':('pmswat','nswaty','pmsatc'),
                      '&mc_swap':('pmswap','pmswmt'),
                      '&mc_cbmc':('rcutin','pmcb','pmcbmt','pmall','nchoi1','nchoi',
                                  'nchoir','nchoih','nchtor','nchbna','nchbnb','icbdir','icbsta',
                                  'rbsmax','rbsmin','avbmc_version','first_bead_to_swap',
                                  'pmbias','pmbsmt','pmbias2','pmfix','lrig','lpresim',
                                  'iupdatefix'),
                      '&mc_simple':('armtra','rmtra','rmrot','tatra','tarot','pmtra',
                                    'pmtrmt','pmromt','pm_atom_tra')}
    namelist_order = ['&mc_shared','&analysis','&mc_volume','&mc_swatch','&mc_swap',
                     '&mc_cbmc','&mc_simple']
    section_order = ['SIMULATION_BOX','MOLECULE_TYPE','SAFE_CBMC','MC_SWAP','MC_SWATCH',
                     'INTERMOLECULAR_EXCLUSION','INTRAMOLECULAR_SPECIAL',
                     'INTRAMOLECULAR_OH15','UNIFORM_BIASING_POTENTIALS',
                     'SPECIFIC_ATOM_TRANSL']
    if len(namelists) != len(namelist_order):
        print('amount of namelists not provided correctly')
        quit()
    elif len(sections) != len(section_order):
#       print('Not enough sections provided')
#       print('- missing sections: ',[i for i in section_order if i not in sections])
#       print('- proceeding without this section')
        section_order = [i for i in section_order if i in sections]
    for NL in namelist_order:
        f.write(NL + '\n')
        my_vars = [i for i in variable_order[NL] if i in data[NL].keys()]
        if len(variable_order[NL]) > len(data[NL].keys()):
            pass
#            print('Expected more variables for namelist: {} '
#                 'including {}'.format(NL, [i for i in variable_order[NL] if i not in data[NL].keys()]))
        elif len(variable_order[NL]) < len(data[NL].keys()):
#            print('More variables from previous input than expected for namelist {} '
#                 'including {}'.format(NL, [i for i in data[NL].keys() if i not in variable_order[NL]]))
#            print(' - using variables anyway')
            my_vars = data[NL].keys()

        for variable in my_vars:
            value = data[NL][variable]
            if type(value) == type(''):
                f.write(makeNewLine(indent,variable,value))
            elif type(value) == type({}):
                val = ''
                for typ in sort_keys(value):
                    val += value[typ] + ' '
                f.write(makeNewLine(indent,variable,val.rstrip(' ')))
            else:
                print("Writefort4 warning: invalid value type %s: %s" % (value, type(value)))
        f.write('/\n\n')
    for SEC in section_order:
        f.write(SEC + '\n')
        if SEC == 'SIMULATION_BOX':
            for box in sort_keys(data[SEC].keys()):
                f.write('! boxlx   boxly   boxlz   rcut  kalp   rcutnn numDimensionIsIstropic lsolid lrect lideal ltwice temperature pressure(MPa)\n')
                for var in ['dimensions', 'rcut', 'defaults', 'temperature', 'pressure']:
                    f.write(data[SEC][box][var] + ' ')
                f.write('\n')
                f.write('! nchain_1 ... nchain_nmolty ghost_particles\n')
                if __debug__: import pprint
                assert (len([i for i in data[SEC][box].keys() if 'mol' in i]) 
                        == int(data['&mc_shared']['nmolty'])), '%s'%pprint.pformat(data[SEC]) + ' error in box%s molecule specs'%box
                for molnum in sort_keys([i for i in data[SEC][box].keys() if 'mol' in i]):
                    f.write(data[SEC][box][molnum] + ' ')
                if 'nghost' in data[SEC][box].keys():
                    f.write(data[SEC][box]['nghost'] + '\n')
                f.write('! inix iniy iniz inirot inimix zshift dshift use_linkcell rintramax\n')
                f.write(data[SEC][box]['initialization data'])
                f.write('\n')
        elif SEC in ['MOLECULE_TYPE','MC_SWATCH']:
            for itype in sort_keys(data[SEC].keys()):
                f.write(data[SEC][itype] + '\n')
        elif SEC == 'MC_SWAP':
            for itype in sort_keys(data[SEC].keys()):
                f.write('! nswapb pmswapb\n')
                f.write('%i '%data[SEC][itype]['nswapb'] +
                        ' '.join(['%6.4fd0'%i for i in data[SEC][itype]['pmswapb']]) + '\n')
                f.write('! box1 box2\n')
                for boxpair in data[SEC][itype]['box1 box2']:
                    f.write(' '.join(['%i'%i for i in boxpair]) + '\n')
        elif SEC == 'INTERMOLECULAR_EXCLUSION':
            for mol1, vals1 in data[SEC].items():
                for unit1, mols2 in vals1.items():
                    for mol2, units2 in mols2.items():
                        for unit2 in units2:
                            f.write('%s %s %s %s\n'%(mol1.strip('mol'), unit1.strip('unit'),
                                                mol2.strip('mol'), unit2.strip('unit')))
        elif SEC == 'INTRAMOLECULAR_OH15':
            for itype in sort_keys(data[SEC].keys()):
                for intra in data[SEC][itype]:
                    f.write(itype.strip('mol') + intra)
        elif (SEC == 'INTRAMOLECULAR_SPECIAL') and (SEC in data.keys()):
            for mol in data[SEC].keys():
                for params in data[SEC][mol]:
                    f.write('%s %s\n'%(mol.strip('mol'), params))
        elif (SEC == 'UNIFORM_BIASING_POTENTIALS') and (SEC in data.keys()):
            for molnum in sort_keys(data[SEC].keys()):
                for box in sort_keys(data[SEC][molnum].keys()):
                    f.write('%8.2f '%data[SEC][molnum][box])
                f.write('\n')
        f.write('END ' + SEC + '\n\n')
    f.close()

def write_restart(data, newfile):
    f = open(newfile,'w')
    f.write(data['number of cycles'])
    f.write(data['max displacement']['atom translation'])
    for box in sort_keys(data['max displacement']['translation'].keys()):
        for molty in sort_keys(data['max displacement']['translation'][box].keys()):
            f.write(data['max displacement']['translation'][box][molty])
            f.write(data['max displacement']['rotation'][box][molty])
    for box in sort_keys(data['max displacement']['fluctuating charge'].keys()):
        for molty in data['max displacement']['fluctuating charge'][box].keys():
            f.write(' ' + data['max displacement']['fluctuating charge'][box][molty] )
        f.write('\n')
    max_displ_volume = ''
    for box in sort_keys(data['max displacement']['volume'].keys()):
        max_displ_volume += ' ' + data['max displacement']['volume'][box]
    f.write(max_displ_volume + '\n')
    for box in sort_keys(data['box dimensions'].keys()):
        if len(data['box dimensions'][box].split()) == 9:
            f.write('0.000000000000000000E+00 '*9 + '\n')
        f.write(data['box dimensions'][box])
    nchain = int(data['nchain'].rstrip('\n'))
    f.write(data['nchain'])
    f.write(data['nmolty'])
    index = 0
    for molty in sort_keys(data['nunit'].keys()):
        index += 1
        f.write('%12s'%data['nunit'][molty])
        if (index > 0) and ((index % 6) == 0):
            f.write('\n')
    if ((index % 6) != 0): f.write('\n')
    if ((len(data['mol types']) != nchain) or (len(data['mol types'])
                                              != len(data['box types']))):
        print('error in writing restart info')
        print('number of molecules not consistent')
        print('error: nchain: ',nchain)
        print('error: mol types: ', len(data['mol types']))
        print('error: box types: ', len(data['box types']))
        print('error: coords: ', len(data['coords']))
        print('quitting...')
        quit()
    for identity in [data['mol types'], data['box types']]:
        index = 0
        for chain in identity:
            index += 1
            f.write('%12s'%chain)
            if (index > 0) and ((index % 6) == 0):
                f.write('\n')
        if ((index % 6) != 0): f.write('\n')
    for mol in data['coords']:
        for bead in mol:
            f.write(bead['xyz'])
            f.write(bead['q'])
    f.close()

def sort_keys(keys):
    my_sort = []
    nums = []
    for key in keys:
        my_str = ''
        my_name = ''
        for letter in key:
            if letter.isdigit():
                my_str += letter
            else:
                my_name += letter
        nums.append(int(my_str))
    for num in sorted(nums):
        for key in keys:
            if key == my_name + '%i'%num:
                my_sort.append(key)
    return my_sort

def makeNewLine(pad,name,val):
    #:: val is a string
    newLine = '%s%-15s = %s\n'%(pad,name,val)
    return newLine
