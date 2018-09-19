#!/usr/bin/env bash


echo -e "\n The script checks the DM value for each observation and makes the parameter file from the last observation file(which usualy is the updated one)"
#prepare a list of the files

zap_files="*.zap"

#pam -mE mod_parfile.par $zap_files
'''
echo -e "\n Create total scrunch on freq,time and polarization and de-dispersion"
pam -FDp -e DFTp $zap_files #$file_list


#echo -e "\n Use the generated DFTp files to create the initial parameter file"
#last_obs=`ls *.DFTp | tail -n 1`
#vap -E $last_obs > parfile.par


echo -e "\n transform the parfile from tempo1 to tempo2"
par="mod_parfile.par"
tempo2 -gr transform $par $par


#echo -e "\n Prepare and check the stem name (e.g B1122+25_D20140125T124533)"
#stem_name=`ls -1 $zap_files`
#echo $stem_name

#looping throgh the list
#for f in $stem_name ; do
#        vap -nc dm $f

#done > initialDM_values.txt
'''
echo -e "\n Start scrunching the frequncy to 8 channels and the time to  10 second sub-int (to be use to generate the first TOAs.tim)"
pam --setnchn 4 --setnsub 10 $zap_files -e zap.F4T10


# Get the templates and the TOAs.tim
dir=`pwd`

echo -e "Run make_templates.py using DFTp files to create the templates (smoothed.prof)"
python2.7 /home/abubakr/MSc_Project/lucasscripts/make_templates.py -datadir $dir -dataext DFTp -forcealign -overwrite -freq 0 -bw 0 -obsnchan 0 -scale 0 -maxsum 0 -noclock

echo -e "\n Run make_toas.py using F8T10 files to create the tim file"
python2.7 /home/abubakr/MSc_Project/lucasscripts/make_toas.py -datadir $dir -dataext T10 -template smoothed.prof -overwrite

