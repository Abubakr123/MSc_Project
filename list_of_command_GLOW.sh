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
        echo -e "\nThese are complete 4 obs"
        ls -1 "$@"
        ls -1 "$1" | ##### awk -F "/|-" '{print $11 "-" $12 "-" $13 }' |
        while read -r; do
            echo "python2.7 "$software_path"reduce_single_station_GLOW_4files.py --indir "$sub_dir" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$list
        done

    elif [ "$#" -eq 3 ]; then
    echo -e "\nchecking if they 3 completed obs or 3 incomlete obs ...\n"
    ### ls -1 "$@" | sort -t. -k3   # this to sort the files in an order

        c_freq1=`psredit -Q -q -c freq "$1"`
        if [ $c_freq1 = $F1 ] || [ $c_freq1 = $F2 ] || [ $c_freq1 = $F3 ]; then
        echo -e "\nFound $c_freq1 = $F1 or $F2 or $F3 ..."
        echo -e "\nThese are compelete 3 obs"
            ls -1 "$@"
            ls -1 "$1" | ###### awk -F "/|-" '{print $11 "-" $12 "-" $13 }' |
            while read -r; do
                echo "python2.7 "$software_path"reduce_single_station_GLOW_3files.py --indir "$sub_dir" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$list
            done

        else
            echo -e "\nFound $c_freq1 != $F1 or $F2 or $F3 ...\n"
            echo -e "\n##### Incomplete 4 observations #####"
            ls -1 "$@"
        fi


    else
    # do things when more than 4 files were found
        echo -e "\n *** Insuficint number of files *** "
        ls -1 "$@"
    fi
done
