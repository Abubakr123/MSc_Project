#!/usr//bin/env bash
dir="$1"
output_dir="$2"
list="$3"
software_path="/home/abubakr/MSc_Project/"


# The  central freq of the complete three files, the new version of DE601,3,5
F1="129.98046875"
F2="153.80859375"
F3="177.63671875"

# loop on all the sub-directories in the maen directories
for sub_dir in "$dir"/*; do
    # choose the file with ar.pscr extension
    set -- "$sub_dir"/*.ar.pscr

    if [ "$#" -eq 4 ]; then
    # do things when 4 files were found
        echo "These are four files"
        ls -1 "$@"
#        ls -1 "$1" | awk -F "/|-" '{print $12 "-" $13 "-" $14 "-" $15}' |
#        while read -r; do
#            echo "python2.7 "$software_path"reduce_single_station_GLOW_4files.py --stem "$REPLY" --indir "$sub_dir" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$list
#        done

    elif [ "$#" -eq 3 ]; then
    # do things when 3 files were found
        echo "These are three files"
        ls -1 "$@" | sort -t. -k3   # this to sort the files in an order

#        ls -1 "$@"
#        ls -1 "$1" | awk -F "/|-" '{print $12 "-" $13 "-" $14 "-" $15}' |
#        while read -r; do
#            echo "python2.7 "$software_path"reduce_single_station_GLOW_3files.py --stem "$REPLY" --indir "$sub_dir" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$list
#        done



#        c_freq1=`psredit -Q -q -c freq "$1"`
#        c_freq2=`psredit -Q -q -c freq "$2"`
#        c_freq3=`psredit -Q -q -c freq "$3"`
#        echo "$c_freq1"

#        if [[ "$c_freq1" == "129.98046875" ]] || [[ "$c_freq1" == "153.80859375" ]] || [[ "$c_freq1" == "177.63671875" ]]; then
#            echo "complete 3 files"
#            ls -1 "@"
#        else
#            echo "incomplete 3 files"
#            ls -1 "$@"
#        fi


    else
    # do things when more than 4 files were found
        echo "Insuficint number of files"
        ls -1 "$@"
    fi
done
