from matplotlib import cm
from matplotlib import colors
import psrchive as psr
from coast_guard import cleaners
from coast_guard import clean_utils
from coast_guard import utils
import os
import sys
from optparse import OptionParser 

parser = OptionParser(usage="%prog <options>", description='Clean files')
parser.add_option("--dir", default='./', type='string', help="State the first BF data directory.")
(options, args) = parser.parse_args()
directory=options.dir
print("Directory: " + directory)
files = []
for file in os.listdir(directory):
    if file.endswith(".tot"):
        files.append(file)
files.sort()
#archives = []
#archives = [psr.Archive_load(directory + file) for file in files]

for file in files:
	archive=archives = psr.Archive_load(directory + file)
	print(archive)
	name=os.path.splitext(file)[0]+'.clean'
	print(name)
	#cleanRFI.unload(name)
	
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
	receiverName = archive.get_receiver_name()
	receptorBasis = archive.get_basis()
	backendName = archive.get_backend_name()
	lowFreq = archive.get_centre_frequency() - archive.get_bandwidth() / 2.0
	highFreq = archive.get_centre_frequency() + archive.get_bandwidth() / 2.0


	print( "nbin             Number of pulse phase bins                 %s" % nBin)
	print( "nchan            Number of frequency channels               %s" % nChan)
	print( "npol             Number of polarizations                    %s" % nPol)
	print( "nsubint          Number of sub-integrations                 %s" % nSubint)
	print( "type             Observation type                           %s" % obsType)
	print( "site             Telescope name                             %s" % telescopeName)
	print( "name             Source name                                %s" % sourceName)
	print( "coord            Source coordinates                         %s%s" % (RA.getHMS(), Dec.getDMS()))
	print( "freq             Centre frequency (MHz)                     %s" % centreFrequency)
	print( "bw               Bandwidth (MHz)                            %s" % bandwidth)
	print( "dm               Dispersion measure (pc/cm^3)               %s" % DM)
	print( "rm               Rotation measure (rad/m^2)                 %s" % RM)
	print( "dmc              Dispersion corrected                       %s" % isDedispersed)
	print( "rmc              Faraday Rotation corrected                 %s" % isFaradayRotated)
	print( "polc             Polarization calibrated                    %s" % isPolCalib)
	print( "scale            Data units                                 %s" % dataUnits)
	print( "state            Data state                                 %s" % dataState)
	print( "length           Observation duration (s)                   %s" % obsDuration)
	print( "rcvr:name        Receiver name                              %s" % receiverName)
	print( "rcvr:basis       Basis of receptors                         %s" % receptorBasis)
	print( "be:name          Name of the backend instrument             %s" % backendName)


	cleanRFI = archive.clone()
	cleaner = cleaners.load_cleaner("surgical")
	cleaner.parse_config_string("chan_numpieces=1,subint_numpieces=1,chanthresh=3,subintthresh=3")
	cleaner.run(cleanRFI)
	name=os.path.splitext(file)[0]+'.clean'
	print("Writing to %s") %name
	cleanRFI.unload(name)


