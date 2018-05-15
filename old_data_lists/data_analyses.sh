#!/bin/bash

Dir="$1"

file=`ls -1 $Dir/*.zap.T | awk -F "/" '{print $5}'`
#pam -D --setnchn 8 $file -e T_8ch

echo $Dir
echo $file

cdfirst_file=`ls $file | head -1`
vap -E $first_file | tail -n +2 > parfile.par

#scrunch to  8 channels
pam -D --setnchn 8 $file -e T_8ch

#single profile DFTp
pam -FDp -e DFTp $file

#add them to creat standard template
#DFTp_files=`ls -1 $Dir/*.zap.DFTp | awk -F "/" '{print $5}'`
#echo $DFTp_files
#psradd -f template.std $DFTp_files

f_scrunch8=`ls -1 $Dir/*.T_8ch | awk -F "/" '{print $5}'`
echo $f_scrunch8
#####echo $standard_temp

paas -l -i -D $first_file
paas_std=`ls -1 $Dir/*.std | awk -F "/" '{print $5}'`

#tempo1 tempo2 transformation
parfile=`ls -1 $Dir/*.par | awk -F "/" '{print $5}'`
parvers=`less $parfile | grep EPHVER | grep -o '[0-9]'`

if [[ $parvers == '2' ]]
then
	echo "parfile version is update for tempo2"
	tempo2 -gr transform $parfile $parfile
fi

echo $paas_std

#getting TOAs
pat -s $paas_std -f tempo2 $f_scrunch8 > toa.tim
tim_file=`ls -1 $Dir/toa.tim | awk -F "/" '{print $5}'`


echo "inhance the par file by fitt for F0 F1 F2"
tempo2 -gr plk -f $parfile $tim_file

echo "Install the newpar file in all teh files"
newpar=`ls -1 $Dir/newpar.par | awk -F "/" '{print $5}'`
pam -mE $newpar $f_scrunch8

echo "Create High S/N observation file"
psradd -T -o high_SN_obs $f_scrunch8

echo "Use the generated high S/N file to create a high-quality standard profile"
paas -i -D high_SN_obs

echo "Make the Residual plot"
pat -Fs $paas_std -f tempo2 $f_scrunch8 > newtim.tim
new_tim_file=`ls -1 $Dir/newtim.tim | awk -F "/" '{print $5}'`

tempo2 -gr plk -f $newpar $new_tim_file

echo "profile variations"
psrsplit -c 1 $f_scrunch8
