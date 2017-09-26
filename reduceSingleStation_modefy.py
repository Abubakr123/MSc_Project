#!/usr/bin/env python

# Copyright (C) 2017 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import os
import sys
import glob
import argparse
import subprocess
import time
import numpy as np
import psrchive as psr
from matplotlib import cm
from matplotlib import colors
from coast_guard import cleaners
from coast_guard import clean_utils
from coast_guard import utils

__version__ = 1.2

directory = './'


def getArchiveInfo(archive):
  """Query archive attributes.
    Input:
      archive: loaded PSRCHIVE archive object.
    Output:
      Print attributes of the archive.
"""
  fileName = archive.get_filename()
  nBin = archive.get_nbin()
  nChan = archive.get_nchan()
  nPol = archive.get_npol()
  nSubint = archive.get_nsubint()
  obsType = archive.get_type()
  telescopeName = archive.get_telescope()
  sourceName = archive.get_source()
  RA = archive.get_coordinates().ra()
  Dec = archive.get_coordinates().dec()
  centreFrequency = archive.get_centre_frequency()
  bandwidth = archive.get_bandwidth()
  DM = archive.get_dispersion_measure()
  RM = archive.get_rotation_measure()
  isDedispersed = archive.get_dedispersed()
  isFaradayRotated = archive.get_faraday_corrected()
  isPolCalib = archive.get_poln_calibrated()
  dataUnits = archive.get_scale()
  dataState = archive.get_state()
  obsDuration = archive.integration_length()
  obsStart = archive.start_time().fracday() + archive.start_time().intday()
  obsEnd = archive.end_time().fracday() + archive.end_time().intday()
  receiverName = archive.get_receiver_name()
  receptorBasis = archive.get_basis()
  backendName = archive.get_backend_name()
  backendDelay = archive.get_backend_delay()
  lowFreq = archive.get_centre_frequency() - archive.get_bandwidth() / 2.0
  highFreq = archive.get_centre_frequency() + archive.get_bandwidth() / 2.0
  print "\nfile             Name of the file                           %s" % fileName
  print "nbin             Number of pulse phase bins                 %s" % nBin
  print "nchan            Number of frequency channels               %s" % nChan
  print "npol             Number of polarizations                    %s" % nPol
  print "nsubint          Number of sub-integrations                 %s" % nSubint
  print "type             Observation type                           %s" % obsType
  print "site             Telescope name                             %s" % telescopeName
  print "name             Source name                                %s" % sourceName
  print "coord            Source coordinates                         %s%s" % (RA.getHMS(), Dec.getDMS())
  print "freq             Centre frequency (MHz)                     %s" % centreFrequency
  print "bw               Bandwidth (MHz)                            %s" % bandwidth
  print "dm               Dispersion measure (pc/cm^3)               %s" % DM
  print "rm               Rotation measure (rad/m^2)                 %s" % RM
  print "dmc              Dispersion corrected                       %s" % isDedispersed
  print "rmc              Faraday Rotation corrected                 %s" % isFaradayRotated
  print "polc             Polarization calibrated                    %s" % isPolCalib
  print "scale            Data units                                 %s" % dataUnits
  print "state            Data state                                 %s" % dataState
  print "length           Observation duration (s)                   %s" % obsDuration
  print "start            Observation start (MJD)                    %.10f" % obsStart
  print "end              Observation end (MJD)                      %.10f" % obsEnd
  print "rcvr:name        Receiver name                              %s" % receiverName
  print "rcvr:basis       Basis of receptors                         %s" % receptorBasis
  print "be:name          Name of the backend instrument             %s" % backendName
  print "be:delay         Backend propn delay from digi. input.      %s\n" % backendDelay

def getZeroWeights(archive, psrsh, verbose = False):
  """Query the number of subint-channels with zeroed weigths 
    (i.e. cleaned) in TimerArchive/PSRFITS file.
       Input:
         archive: loaded PSRCHIVE archive object.
         psrsh: name of psrsh file
         verbose: verbosity flag
       Output:
         Writes out psrsh file with zap commands.
"""
  weights = archive.get_weights()
  (nSubint, nChan) = weights.shape
  print "%s has %s subints and %s channels." % (archive.get_filename(), nSubint, nChan)
  psrshFilename = archive.get_filename() + ".psh"
  psrshFile = open(psrshFilename, "w")
  psrshFile.write("#!/usr/bin/env psrsh\n\n")
  psrshFile.write("# Run with psrsh -e <ext> <script>.psh <archive>.ar\n\n")
  i = j = counter = spectrum = 0
  emptyChannels = [i for i in range(nChan)]
  for i in range(nSubint):
    spectrum = 0
    del emptyChannels[:]
    for j in range(nChan):
      if weights[i][j] == 0.0:
        counter += 1
        spectrum += 1
        emptyChannels.append(j)
    if verbose:
      percentSubint = (float(spectrum) / float(nChan)) * 100
      print "Subint %s has %s channels (%.2f%%) set to zero. %s" % (i, spectrum, percentSubint, emptyChannels)
    for k in range(len(emptyChannels)):
      #print "zap such %d,%d" % (i, empty_channels[k])
      np.savetxt(psrshFile, np.c_[i, emptyChannels[k]], fmt='zap such %d,%d')
  totalPercent = (float(counter)/float(weights.size)) * 100
  print "%s data points out of %s with weights set to zero." % (counter, weights.size)
  print "%.2f%% data points set to zero." % (totalPercent)

# Main body of the script.
if __name__=="__main__":
  # Parsing the command line options.
  parser = argparse.ArgumentParser(usage = "reduceSingleStation.py --stem <stemName> [options]",
                                   description = "Reduce LOFAR single station TimerArchive data. Version %s" % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = "Copyright (C) 2017 by Maciej Serylak")
  parser.add_argument("--indir", default='.', dest = "inputDir", metavar = "<inputDir>", help="specify the input data directory.")
  parser.add_argument("--outdir", dest = "outputDir", metavar = "<outputDir>", default = "" , help = "specify output directory")
  parser.add_argument("--eph", dest = "ephemFile", metavar = "<ephemFile>", default = "" , help = "use ephemeris file to update archives")
  parser.add_argument("--psrsh", dest = "psrshSave", action="store_true" , help="write zap commands to psrsh script file")
  parser.add_argument("--stem", dest = "stemName", metavar = "<stemName>", default = "", help = "filename stem PSR_DYYYYMMDDTHHMMSS")
  parser.add_argument('-t', '--tscr', dest='tscr', action='store_true', help='time scrunch and write out the file')
  args = parser.parse_args() # Reading command line options.


  # Start script timing
  scriptStartTime = time.time()

  #sign into the inputDir
  workDir = directory 
  workDir = os.chdir(args.inputDir) #to change the directory to argument passed fr '--inputDir'
  #print os.getcwd()
  

  # Check for stemName presence.
  if not args.stemName:
    print parser.description, "\n"
    print "usage:", parser.usage, "\n"
    print parser.epilog
    sys.exit(0)

  # Check for outputDir presence and validate writing permissions.
  outputDir = args.outputDir
  if not outputDir:
    print "\nOption --outdir not specified. Selecting current working directory.\n"
    outputDir = os.getcwd()
    if os.access(outputDir, os.W_OK):
      pass
      print outputDir
    else:
      print "\nCurrent directory without write permissions. Exiting script.\n"
      sys.exit(0)


  # Assign working directory.
  workDir = os.getcwd()
  print workDir


  # Check for presence of all (4) files from LOFAR single station backend.
  # It is assumed that number or channels, sub-integrations, phase bins and
  # polarisations are the same. It is also assumed that file name format is
  # PSR_DYYYYMMDDTHHMMSS_CHAN_SUB.ar. More through checks are on TODO list.
  stemName = args.stemName
  fileNames = glob.glob( stemName + "*.ar")
  fileNames.sort()
  #print fileNames
  if len(fileNames) == 4:
    pass
    print "Using following data files:"
    print "%s\n%s\n%s\n%s" % (fileNames[0], fileNames[1], fileNames[2], fileNames[3])
  elif len(fileNames) <= 3:
    print "\nFound only %d archive files. Exiting script.\n" % len(fileNames)
    sys.exit(0)
  elif len(fileNames) > 4:
    print "\nFound %d archive files. Exiting script.\n" % len(fileNames)
    sys.exit(0)

  # Read ephemeris and check if it conforms to standard (has EPHVER in it).
  # This is very rudimentary check. One should check for minimal set of values
  # present in the par file. More through checks are on TODO list.
  ephemFile = args.ephemFile
  if not ephemFile:
    print "\nOption --eph not specified. Continuing without updating ephemeris.\n"
    updateEphem = False
   
  else:
    if "EPHVER" not in open(ephemFile).read():
      print "\nProvided file does not conform to ephemeris standard. Exiting script.\n"
      sys.exit(0)
    else:
      updateEphem = True
      print "\nProvided file %s does conform to ephemeris standard.\n" % ephemFile

  
  # Add data files together.
  addedFile = stemName + ".ar"
  print "\nAdding data files to create %s\n" % addedFile
  cmd = ["psradd", "-m", "time", "-q", "-R", "-o", addedFile, fileNames[0], fileNames[1], fileNames[2], fileNames[3]]
  pipe = subprocess.Popen(cmd, shell=False, cwd=workDir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  (stdoutdata, stderrdata) = pipe.communicate()
  returnCode = pipe.returncode
  if returnCode != 0:
    print "\nAdding files unsuccessful. Exiting script\n"
    sys.exit(0)
  

  # Reading data.
  archive = psr.Archive_load(workDir + "/" + addedFile)
  getArchiveInfo(archive)

  
  if updateEphem:
    print "\nUpdating ephemeris in: %s\n" % addedFile
    archive.set_ephemeris(ephemFile)
    archive.unload()
 
  # Zapping first 39 channels and last 49 channels. Checking if
  # frequency range is as expected (109.9609375 <= freq <= 187.890625).
  firstFrequency = 109.9609375
  lastFrequency = 187.890625
  channelBW = 0.1953125
  nChanFinal = 400
  expectedFrequencyTable = np.arange(firstFrequency, lastFrequency + channelBW, channelBW)
  archiveFrequencyTable = np.zeros(nChanFinal)
  for chan in np.arange(0, nChanFinal, 1):
    archiveFrequencyTable[chan] = archive.get_first_Integration().get_Profile(0, chan + 39).get_centre_frequency()
  if np.array_equal(archiveFrequencyTable, expectedFrequencyTable):
    pass
    print "Frequency table correct!"
  else:
    print "\nUnexpected frequency range. Exiting script.\n"
    sys.exit(0)
  archive.remove_chan(0, 38)
  archive.remove_chan(400, 448)
  archive.unload()



  # Clean archive from RFI and save zap commands to psrsh file.
  cleanRFI = psr.Archive_load(addedFile)
  cleaner = cleaners.load_cleaner("surgical")
  surgicalDefaultParams = "chan_numpieces=1,subint_numpieces=1,chanthresh=3,subintthresh=3"
  cleaner.parse_config_string(surgicalDefaultParams)
  print "\nCleaning archive from RFI.\n"
  cleaner.run(cleanRFI)
  getArchiveInfo(cleanRFI)

  #pol,freq and time scrunch the clean file and write the result file as output
  print '\n FTp scrunching the cleaned file \n' 
  p_scrunch = cleanRFI.clone()
  p_scrunch.pscrunch()
  p_scrunch.tscrunch_to_nsub(6)
  p_scrunch.fscrunch_to_nchan(8)

  #produce time,freq.pol scrunch and dedispers  and write it in the output
  FTDp_scr = cleanRFI.clone()
  FTDp_scr.dedisperse()  
  FTDp_scr.pscrunch()
  FTDp_scr.tscrunch()
  FTDp_scr.fscrunch()

  #produce time scrunch and dedispers  and write it in the output
  # Prepare de-dispersed and freq. resolved average profile.
  if args.tscr:
      tscrunch_archive = raw_archive.clone()
      tscrunch_archive.dedisperse()
      tscrunch_archive.tscrunch()
      if args.clean_rfi:
          tscrunch_archive.unload(output_dir + '/' + filename_stem + '.ar.zap.DT')
      else:
           tscrunch_archive.unload(output_dir + '/' + filename_stem + '.ar.DT')

  TD_scr = cleanRFI.clone()
  TD_scr.dedisperse()  
  TD_scr.pscrunch()
  TD_scr.tscrunch()

  #produce freq scrunch and dedispers and write it in the output
  FD_scr = cleanRFI.clone()
  FD_scr.dedisperse()
  FD_scr.pscrunch()
  FD_scr.fscrunch()
  
  if args.psrshSave:
    psrshFilename = addedFile + ".psh"
    print psrshFilename
    getZeroWeights(cleanRFI, psrshFilename)

  print "\nSaving data to file %s\n" % (addedFile + ".zap")
  cleanRFI.unload(addedFile + ".zap")

  print '\n save data to file %s \n' % (addedFile + '.zap.F8T6p')
  p_scrunch.unload( outputDir + '/' + addedFile + ".zap.F8T6p" )


  print '\n scrunching on the time and save to file %s \n' % (addedFile + '.zap.TpD')
  TD_scr.unload( outputDir + '/' + addedFile + ".zap.TpD" )

  print '\n scrunching on the frequancy and save to %s \n' % (addedFile + '.zap.FpD')
  FD_scr.unload(outputDir + '/' + addedFile + ".zap.FpD" )

  print '\n Scrunching on time and frequancy and save to %s \n' % (addedFile + '.zap.FTpD')
  FTDp_scr.unload(outputDir + '/' + addedFile + ".zap.FTpD" )



  scriptEndTime = time.time()
  print "\nScript running time: %.1f s.\n" % (scriptEndTime - scriptStartTime)





