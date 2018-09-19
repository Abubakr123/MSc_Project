#!/usr/bin/env/bash

dir=`pwd`

#mkdir redo_second_loop
cd redo_second_loop


# Start tempo2 to check and adjust the parameters
echo -e "\n Check and adjust the parameters in the initial parfile and get new_parfil.par"
#tempo2 -gr plk -npsr 1 -nofit -nobs 30000 -f $dir/mod_parfile.par -setup /home/abubakr/MSc_Project/mypsr/script/plk_setup_fr606_embrace.dat $dir/TOAs.tim

#echo -e "\n The end of loop 1 and staart loop 2"

# Install the new_parfile.par on all the original files
# This will update the parameters and the dm header and scrunch to 8 channels and scrunch all the time

echo -e "\n Start updating the obs with the new parfile and dm and F8T1 scrunch"
pam --update_dm -mE $dir/mod_parfile.par $dir/*.pscr.zap --setnchn 4 -T -e zap.F4T1


#ransform the ephemerides from tempo1 version to tempo2 version
echo -e "\n Starting the transformation"
parvers=`less $dir/mod_parfile.par | grep EPHVER | grep -o '[0-9]'`
if [[ $parvers == '2' ]]
then
	echo -e "\n Update the parfile version to tempo2"
	tempo2 -gr transform $dir/mod_parfile.par $dir/mod_parfile.par
fi

# Run make_templates,toas.py to produce the profiles and TOAs files.

pam -DFp $dir/*.F4T1 -e DFTp

python2.7 /home/abubakr/MSc_Project/lucasscripts/make_templates.py -datadir $dir -dataext DFTp -sortsnr -overwrite -freq 0 -bw 0 -obsnchan 0 -scale 0 -maxsum 0 -noclock
python2.7 /home/abubakr/MSc_Project/lucasscripts/make_toas.py -datadir $dir -dataext F4T1 -plotres -template $dir/redo_second_loop/smoothed.prof -overwrite



echo -e "\n############### Apply trimtim.py to cut of the outlayers of the TOAs.tim and producing TOAs.tim_trimtim ###############\n"
python2.7 ~/MSc_Project/caterina_trimtim.py -o $dir/redo_second_loop/TOAs.tim -e $dir/mod_parfile.par


# check the result of caterina script
tempo2 -gr plk  -f $dir/mod_parfile.par -setup /home/abubakr/MSc_Project/mypsr/script/plk_setup_fr606_embrace.dat $dir/redo_second_loop/TOAs.tim_trimtim

echo -e "\n Use tempo2 EPHVER to calculate the DM variations"
tail -n +2 $dir/redo_second_loop/TOAs.tim_trimtim | grep -v "C "| cut -d " " -f3 | cut -d "." -f1 | awk '{print ($1)" "($1)+1" a a"}' > strides0.dat
uniq -c $dir/redo_second_loop/strides0.dat  | awk '{ print $2" " $3" " $4 " " $5}' > strides.dat

tempo2 -gr dm -t $dir/redo_second_loop/strides.dat -npsr 1 -nobs 390000 -f $dir/mod_parfile.par $dir/redo_second_loop/TOAs.tim_trimtim

