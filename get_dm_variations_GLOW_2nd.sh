#!/usr/bin/env/bash

dir=`pwd`
zap_files="$dir/*.zap"

mkdir Second_loop
cd Second_loop

# Start tempo2 to check and adjust the parameters
echo -e "\n############### Check and adjust the parameters in the initial parfile and get new_parfil.par (in case of the bad sample, you can work on a bunch of phase connected TOAs by fitting F0, F1, DM and position) ###############\n"
#tempo2 -gr plk -npsr 1 -nofit -nobs 30000 -f $dir/new_parfile.par -setup /home/abubakr/MSc_Project/mypsr/script/plk_setup_fr606_embrace.dat $dir/TOAs.tim

echo -e "\n############### Refined the the model on all the TOAs ###############\n"
#tempo2 -gr plk -npsr 1 -nofit -nobs 30000 -f $dir/Second_loop/new_parfile.par -setup /home/abubakr/MSc_Project/mypsr/script/plk_setup_fr606_embrace.dat $dir/TOAs.tim


echo -e "\n############### The end of loop 1 and staart loop2 ###################\n"

#Transform the ephemerides from tempo1 version to tempo2 version
echo -e "\n Starting the transformation  \n"
parvers=`less $dir/Second_loop/new_parfile.par | grep EPHVER | grep -o '[0-9]'`
if [[ $parvers == '2' ]]
then
        echo -e "\nUpdate the parfile version to tempo2"
        tempo2 -gr transform $dir/Second_loop/new_parfile.par $dir/Second_loop/new_parfile.par
fi


# Install the new_parfile.par on all the original files
# This will update the parameters and the dm header and scrunch to 8 channels and scrunch to the full time

echo -e "\n############### Start updating the obs with the new parfile and dm and F8T1 & F6T1 scrunch ###############\n"

for file in $zap_files; do
    nchan=`psredit -Q -q -c nchan "$file"`
    if [ "$nchan" -eq 400 ]; then
        ls -1 $file
        pam --update_dm -E $dir/Second_loop/new_parfile.par $file --setnchn 4 -T -e zap.F4.T1
    else
        pam --update_dm -E $dir/Second_loop/new_parfile.par $file --setnchn 4 -T -e zap.F4.T1
    fi
done



echo -e "\n############### Get the total scrunch and run make_templates,toas.py to produce the profiles and TOAs files ###############\n"
pam -DFp $dir/*.T1 -e T1.DFTp
python2.7 /home/abubakr/MSc_Project/lucasscripts/make_templates.py -datadir $dir -dataext T1.DFTp -sortsnr -overwrite -freq 0 -bw 0 -obsnchan 0 -scale 0 -maxsum 0 -noclock
python2.7 /home/abubakr/MSc_Project/lucasscripts/make_toas.py -datadir $dir -dataext T1 -plotres -template $dir/Second_loop/smoothed.prof -overwrite


echo -e "\n############### Apply trimtim.py to cut of the outlayers of the TOAs.tim and producing TOAs.tim_trimtim ###############\n"
python2.7 ~/MSc_Project/caterina_trimtim.py -o TOAs.tim -e new_parfile.par


echo -e "\n############### Recall the PSR.trimtim Use tempo2 EPHVER to calculate the DM variations ###############\n"
tail -n +2 $dir/Second_loop/TOAs.tim_trimtim | grep -v "C "| cut -d " " -f3 | cut -d "." -f1 | awk '{print ($1)" "($1)+1" a a"}' > strides0.dat
uniq -c $dir/Second_loop/strides0.dat  | awk '{ print $2" " $3" " $4 " " $5}' > strides.dat
tempo2 -gr dm -t $dir/Second_loop/strides.dat -npsr 1 -nobs 300000 -f $dir/Second_loop/new_parfile.par $dir/Second_loop/TOAs.tim_trimtim


