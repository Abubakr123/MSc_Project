#!/usr/bin/env python

# Copyright (C) 2017 by Maciej Serylak and Abubakr Yagob
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import os
import sys
import glob
import time
import argparse
import subprocess
import numpy as np
import psrchive
from coast_guard import cleaners


def get_archive_info(archive):
    """Query archive attributes.

    Input:
        archive: loaded PSRCHIVE archive object.
    Output:
        Print attributes of the archive.
    """
    filename = archive.get_filename()
    nbin = archive.get_nbin()
    nchan = archive.get_nchan()
    npol = archive.get_npol()
    nsubint = archive.get_nsubint()
    obs_type = archive.get_type()
    telescope_name = archive.get_telescope()
    source_name = archive.get_source()
    ra = archive.get_coordinates().ra()
    dec = archive.get_coordinates().dec()
    centre_frequency = archive.get_centre_frequency()
    bandwidth = archive.get_bandwidth()
    DM = archive.get_dispersion_measure()
    RM = archive.get_rotation_measure()
    is_dedispersed = archive.get_dedispersed()
    is_faraday_rotated = archive.get_faraday_corrected()
    is_pol_calib = archive.get_poln_calibrated()
    data_units = archive.get_scale()
    data_state = archive.get_state()
    obs_duration = archive.integration_length()
    obs_start = archive.start_time().fracday() + archive.start_time().intday()
    obs_end = archive.end_time().fracday() + archive.end_time().intday()
    receiver_name = archive.get_receiver_name()
    receptor_basis = archive.get_basis()
    backend_name = archive.get_backend_name()
    backend_delay = archive.get_backend_delay()
    # low_freq = archive.get_centre_frequency() - archive.get_bandwidth() / 2.0
    # high_freq = archive.get_centre_frequency() + archive.get_bandwidth() / 2.0
    print 'file             Name of the file                           %s' % filename
    print 'nbin             Number of pulse phase bins                 %s' % nbin
    print 'nchan            Number of frequency channels               %s' % nchan
    print 'npol             Number of polarizations                    %s' % npol
    print 'nsubint          Number of sub-integrations                 %s' % nsubint
    print 'type             Observation type                           %s' % obs_type
    print 'site             Telescope name                             %s' % telescope_name
    print 'name             Source name                                %s' % source_name
    print 'coord            Source coordinates                         %s%s' % (ra.getHMS(), dec.getDMS())
    print 'freq             Centre frequency (MHz)                     %s' % centre_frequency
    print 'bw               Bandwidth (MHz)                            %s' % bandwidth
    print 'dm               Dispersion measure (pc/cm^3)               %s' % DM
    print 'rm               Rotation measure (rad/m^2)                 %s' % RM
    print 'dmc              Dispersion corrected                       %s' % is_dedispersed
    print 'rmc              Faraday Rotation corrected                 %s' % is_faraday_rotated
    print 'polc             Polarization calibrated                    %s' % is_pol_calib
    print 'scale            Data units                                 %s' % data_units
    print 'state            Data state                                 %s' % data_state
    print 'length           Observation duration (s)                   %s' % obs_duration
    print 'start            Observation start (MJD)                    %.10f' % obs_start
    print 'end              Observation end (MJD)                      %.10f' % obs_end
    print 'rcvr:name        Receiver name                              %s' % receiver_name
    print 'rcvr:basis       Basis of receptors                         %s' % receptor_basis
    print 'be:name          Name of the backend instrument             %s' % backend_name
    print 'be:delay         Backend propn delay from digi. input.      %s\n' % backend_delay


def get_zero_weights(archive, psrsh, verbose=False):
    """Get zero-weighted subints/channels from archive file.

    Query the number of subints and channels with
    zeroed weights (i.e. cleaned) and create psrsh
    script with zapped subints and channels from
    TimerArchive/PSRFITS folded data.
    Input:
        archive: loaded PSRCHIVE archive object.
        psrsh: name of psrsh file
        verbose: verbosity flag
    Output:
        Writes out psrsh file with zap commands.
    """
    weights = archive.get_weights()
    (nsubint, nchan) = weights.shape
    if verbose:
        print '%s has %s subints and %s channels.' % (archive.get_filename(), nsubint, nchan)
    psrsh_file = open(psrsh, 'w')
    psrsh_file.write('#!/usr/bin/env psrsh\n\n')
    psrsh_file.write('# Run with psrsh -e <ext> <script>.psh <archive>.ar\n\n')
    i = j = total_empty_channels = subint_empty_channels = 0
    subint_empty_channels_list = [k for k in range(nchan)]
    for i in range(nsubint):
        subint_empty_channels = 0
        del subint_empty_channels_list[:]
        for j in range(nchan):
            if weights[i][j] == 0.0:
                total_empty_channels += 1
                subint_empty_channels += 1
                subint_empty_channels_list.append(j)
        if verbose:
            subint_emtpy_percentage = (float(subint_empty_channels) / float(nchan)) * 100
            print 'Subint %s has %s channels (%.2f%%) set to zero. %s' % (i, subint_empty_channels, subint_emtpy_percentage, subint_empty_channels_list)
        for k in range(len(subint_empty_channels_list)):
            # print 'zap such %d,%d' % (i, subint_empty_channels_list[k])
            np.savetxt(psrsh_file, np.c_[i, subint_empty_channels_list[k]], fmt='zap such %d,%d')
    total_empty_percentage = (float(total_empty_channels) / float(weights.size)) * 100
    if verbose:
        print '%s data points out of %s with weights set to zero.' % (total_empty_channels, weights.size)
        print '%.2f%% data points set to zero.' % (total_empty_percentage)


def replace_nth(string, source, target, position):
    """Replace N-th occurrence of a sub-string in a string.
    TODO: add error if no instance found.
    Input:
        string: string to search in.
        source: sub-string to replace.
        target: sub-string to replace with.
        position: nth occurrence of source to replace.
    Output:
        String with replaced sub-string.
    """
    indices = [i for i in range(len(string) - len(source) + 1) if string[i:i + len(source)] == source]
    if len(indices) < position:
        # or maybe raise an error
        return
    # Can't assign to string slices. So, let's listify.
    string = list(string)
    # Do position-1 because we start from the first occurrence of the string, not the 0-th.
    string[indices[position - 1]:indices[position - 1] + len(source)] = target
    return ''.join(string)


# Main body of the script.
if __name__ == '__main__':
    # Parsing the command line options.
    parser = argparse.ArgumentParser(usage='reduce_single_station.py --stem=<stem_name> [options]',
                                     description='Reduce LOFAR single station TimerArchive/PSRFITS data.',
                                     formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=250),
                                     epilog='Copyright (C) 2017 by Maciej Serylak and Abubakr Yagob')
    parser.add_argument('-s', '--stem', dest='stem_name', metavar='<stem_name>', default='', help='filename stem PSR_DYYYYMMDDTHHMMSS')
    parser.add_argument('-i', '--indir', dest='input_dir', metavar='<input_dir>', default='', help='specify input directory')
    parser.add_argument('-o', '--outdir', dest='output_dir', metavar='<output_dir>', default='', help='specify output directory')
    parser.add_argument('-e', '--eph', dest='ephem_file', metavar='<ephem_file>', default='', help='use ephemeris file to update archives')
    # parser.add_argument('-n', '--ntscr', dest='tscr_nsub', metavar='<ntscr>', nargs=1, help='dedisperse, time scrunch to n-subints and write out the file')
    parser.add_argument('-t', '--tscr', dest='tscr', action='store_true', help='time scrunch and write out the file')
    parser.add_argument('-f', '--fscr', dest='fscr', action='store_true', help='frequency scrunch and write out the file')
    parser.add_argument('-c', '--clean', dest='clean_rfi', action='store_true', help='clean data from RFI using CoastGuard\'s clean.py')
    parser.add_argument('-p', '--psrsh', dest='psrsh_save', action='store_true', help='write zap commands to psrsh script file')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='verbose mode')
    args = parser.parse_args()  # Reading command line options.

    # Start timing the script.
    script_start_time = time.time()

    # Check for stem_name presence.
    if not args.stem_name:
        print parser.description, '\n'
        print 'Usage:', parser.usage, '\n'
        print parser.epilog
        sys.exit(2)

    # Check for input_dir presence and validate read, write execute permissions.
    if not args.input_dir:
        if args.verbose:
            print '\nOption --indir not specified. Selecting current working directory.\n'
        input_dir = os.getcwd()
    else:
        if os.access(args.input_dir, os.F_OK):
            input_dir = args.input_dir
        else:
            raise RuntimeError('Input directory does not exist.')
        if os.access(input_dir, os.R_OK) and os.access(input_dir, os.X_OK): # and os.access(input_dir, os.R_OK):
            pass
        else:
            raise RuntimeError('Input directory without read, write and execute permissions.')

    # Check for output_dir presence and validate read, write execute permissions.
    if not args.output_dir:
        if args.verbose:
            print '\nOption --outdir not specified. Selecting input directory.\n'
        output_dir = args.input_dir
    else:
        if os.access(args.output_dir, os.F_OK):
            output_dir = args.output_dir
        else:
            raise RuntimeError('Output directory does not exist.')
        if os.access(args.output_dir, os.W_OK) and os.access(args.output_dir, os.X_OK) and os.access(args.output_dir, os.R_OK):
            pass
        else:
            raise RuntimeError('Output directory without read, write and execute permissions.')

    # Read ephemeris and check if it conforms to standard (has EPHVER in it).
    # This is very rudimentary check. One should check for minimal set of values
    # present in the par file. More through checks are on TODO list.
    ephem_file = args.ephem_file
    if not ephem_file:
        if args.verbose:
            print '\nOption --eph not specified. Continuing without updating ephemeris.\n'
        update_ephem = False
    else:
        if 'EPHVER' not in open(ephem_file).read():
            raise RuntimeError('Provided file does not conform to ephemeris standard.')
        else:
            update_ephem = True

    # Check for TimerArchive/PSRFITS files presence and add them together.
    stem_name = args.stem_name
    input_dir = args.input_dir
    input_files = glob.glob(input_dir + '/' + stem_name + '*.ar')
    input_files.sort()
    if len(input_files) == 4:
        pass
        if args.verbose:
            print 'Using following data files:'
            print '%s\n%s\n%s\n%s' % (input_files[0], input_files[1], input_files[2], input_files[3])
    elif len(input_files) <= 3:
        raise RuntimeError('Insufficient number of matching TimerArchive/PSRFITS files.')
    elif len(input_files) > 4:
        raise RuntimeError('Exceeding number of matching TimerArchive/PSRFITS files.')
    added_filename = output_dir + '/' + stem_name + '.ar.pscr'
    if args.verbose:
        print '\nAdding data files to create %s.ar.pscr in %s\n' % (stem_name, output_dir)
    cmd = ['psradd', '-jpscrunch', '-m', 'time', '-q', '-R', '-o', added_filename, input_files[0], input_files[1], input_files[2], input_files[3]]
    pipe = subprocess.Popen(cmd, shell=False, cwd=input_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stdoutdata, stderrdata) = pipe.communicate()
    return_code = pipe.returncode
    if return_code != 0:
        raise RuntimeError('Adding files unsuccessful.')

    # Read new file.
    raw_archive = psrchive.Archive_load(added_filename)
    if args.verbose:
        get_archive_info(raw_archive)

    # Update ephemeris and write out the file.
    if update_ephem:
        if args.verbose:
            print '\nUpdating ephemeris in: %s\n' % raw_archive.get_filename()
        raw_archive.set_ephemeris(ephem_file)

    # Zapping first 39 channels and last 49 channels. Checking if
    # frequency range is as expected (109.9609375 <= freq <= 187.890625).
    first_frequency = 109.9609375
    last_frequency = 187.890625
    channel_bw = 0.1953125
    nchan_final = 400
    expected_frequency_table = np.arange(first_frequency, last_frequency + channel_bw, channel_bw)
    archive_frequency_table = np.zeros(nchan_final)
    for chan in np.arange(0, nchan_final, 1):
        archive_frequency_table[chan] = raw_archive.get_first_Integration().get_Profile(0, chan + 39).get_centre_frequency()
    if np.array_equal(archive_frequency_table, expected_frequency_table):
        pass
        if args.verbose:
            print "\nFrequency table correct!\n"
    else:
        raise RuntimeError('Unexpected frequency range.')
    raw_archive.remove_chan(0, 38)
    raw_archive.remove_chan(400, 448)
    raw_archive.unload()

    # Clean archive from RFI and save zap commands to psrsh file.
    if args.clean_rfi:
        cleaner = cleaners.load_cleaner('surgical')
        surgical_parameters = 'chan_numpieces=1,subint_numpieces=1,chanthresh=3,subintthresh=3'
        cleaner.parse_config_string(surgical_parameters)
        if args.verbose:
            print '\nCleaning archive from RFI.\n'
        cleaner.run(raw_archive)
        if args.psrsh_save:
            psrsh_filename = output_dir + '/' + stem_name + '.psh'
            if args.verbose:
                print '\nSaving zap commands to psrsh script: %s\n' % psrsh_filename
            get_zero_weights(raw_archive, psrsh_filename)
        print '\nSaving data to file %s\n' % (stem_name + '.ar.pscr.zap')
        raw_archive.unload(output_dir + '/' + stem_name + '.ar.pscr.zap')

    # Prepare freq. resolved average profile.
    if args.tscr:
        tscrunch_archive = raw_archive.clone()
        tscrunch_archive.tscrunch()
        if args.clean_rfi:
            tscrunch_archive.unload(output_dir + '/' + stem_name + '.ar.pscr.zap.T')
        else:
            tscrunch_archive.unload(output_dir + '/' + stem_name + '.ar.pscr.T')

    # Prepare time resolved average profile.
    if args.fscr:
        fscrunch_archive = raw_archive.clone()
        fscrunch_archive.fscrunch()
        if args.clean_rfi:
            fscrunch_archive.unload(output_dir + '/' + stem_name + '.ar.pscr.zap.F')
        else:
            fscrunch_archive.unload(output_dir + '/' + stem_name + '.ar.pscr.F')

#    if args.tscr_nsub:
#        ntscrunch_archive = raw_archive.clone()
#        ntscrunch_archive.tscrunch_to_nsub(int(args.tscr_nsub[0]))
#        if args.clean_rfi:
#            raw_archive.unload(output_dir + '/' + stem_name + '.ar.pscr.zap.T' + args.tscr_nsub[0])
#        else:
#            raw_archive.unload(output_dir + '/' + stem_name + '.ar.pscr.T' + args.tscr_nsub[0])

    # End timing the script and output running time.
    script_end_time = time.time()
    print '\nScript running time: %.1f s.\n' % (script_end_time - script_start_time)
