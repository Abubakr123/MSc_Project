#!/usr//bin/env bash
dir="$1"
output_dir="$2"
list="$3"
software_path="/home/abubakr/MSc_Project/"



#checking and creating a new directory to the outputs

echo "Enter the output Directory Name: " $output_dir

if [[ ! -d "$output_dir" ]]
then
        echo "Directory doesn't exist. Creating new directory"
        mkdir $output_dir 
        echo "The new directory is: " $output_dir
else
        echo "Directory exists: " $output_dir

fi




# loop on all the sub-directories in the maen directories
for sub_dir in "$dir"/*; do
    # choose the file with ar.pscr extension
    set -- "$sub_dir"/*.ar.pscr
    

    if [ "$#" -eq 4 ]; then
    # do things when 4 files were found
        input_dir=`echo "$sub_dir" | awk -F "/|" '{print "/" $2 "/" $3 "/" $4 "/" $5 "/" $6}'`
        echo "$input_dir"
        echo "These are four files"
        ls -1 "$@"
#        stem=`ls -1 $1`
#        echo "stem"
#        mjd=`psredit -Q -q -c int[0]:mjd "$@" |  awk  '{print substr($1,1,8)}'`
#        mjd1=`psredit -Q -q -c int[0]:mjd "$1" |  awk  '{print substr($1,1,8)}'`
#        if [ "mjd" -eq "mjd1" ]; then
#            stem=`$@`
        ls -1 "$1"  | awk -F "/|-" '{print  $8 "-" $9 "-" $10 "-" $11 "/" $12 "-" $13 "-" $14 }' |
        while read -r; do
            echo "python2.7 "$software_path"reduce_single_station_GLOW_4files.py --stem "$REPLY" --indir "$input_dir" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$list
        done
#        fi
#    elif [ "$#" -eq 3 ]; then
#    # do things when 3 files were found
#        echo "These are three files"
#        ls -1 "$@"
#        psredit -Q -q -c int[0]:mjd "$1" |  awk  '{print substr($1,1,8)}' |
#        while read -r; do
#            echo "python2.7 "$software_path"reduce_single_station_GLOW_3files.py --stem "$REPLY" --indir "$sub_dir" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$list
#        done

    else
    # do things when more than 4 files were found
        echo "Insuficint number of files"
        ls -1 "$@"
#        rm "$@"
    fi
done
