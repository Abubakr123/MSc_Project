#!/usr/bin/env bash

dir=`pwd`
zap_files="$dir/*.zap"

mkdir second_loop_trimtim
cd second_loop_trimtim

dir2=`pwd`


tempo2 -gr plk -npsr 1 -nofit -nobs 30000 -f ../parfile.par -setup /home/abubakr/MSc_Project/mypsr/script/plk_setup_fr606_embrace.dat ../TOAs.tim


echo -e "\n############### Refined the the model on all the TOAs ###############\n"
tempo2 -gr plk -npsr 1 -nofit -nobs 30000 -f new_parfile.par -setup /home/abubakr/MSc_Project/mypsr/script/plk_setup_fr606_embrace.dat $dir/TOAs.tim


echo -e "\n############### The end of loop 1 and staart loop2 ###################\n"

#Transform the ephemerides from tempo1 version to tempo2 version
echo -e "\nUpdate the parfile version to tempo2"
tempo2 -gr transform new_parfile.par new_parfile.par


pam --update_dm -mE new_parfile.par $dir/*.F8T1 -u $dir2
pam -DFp $dir2/*.F8T1 -e DFTp -u $dir2

python2.7 /home/abubakr/MSc_Project/lucasscripts/make_templates.py -datadir $dir2 -dataext DFTp -sortsnr -overwrite -freq 0 -bw 0 -obsnchan 0 -scale 0 -maxsum 0 -noclock
python2.7 /home/abubakr/MSc_Project/lucasscripts/make_toas.py -datadir $dir2 -dataext F8T1 -plotres -template $dir2/smoothed.prof -overwrite

python2.7 ~/MSc_Project/caterina_trimtim.py -o TOAs.tim -e new_parfile.par


tail -n +2 TOAs.tim_trimtim | grep -v "C "| cut -d " " -f3 | cut -d "." -f1 | awk '{print ($1)" "($1)+1" a a"}' > strides0.dat
uniq -c strides0.dat  | awk '{ print $2" " $3" " $4 " " $5}' > strides.dat
tempo2 -gr dm -t strides.dat -npsr 1 -nobs 300000 -f new_parfile.par TOAs.tim_trimtim

mv dmvals.dat dmvals_trimtim.dat
