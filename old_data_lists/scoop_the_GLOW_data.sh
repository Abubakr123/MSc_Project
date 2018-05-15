#!/bin/bash

list="$2"
topdir="$1"

for dir in "$topdir"/*; do
    set -- "$dir"/*.pscr

    if [ "$#" -eq 1 ] && [ ! -f "$1" ]; then
        # do things when no files were found
        # "$1" will be the pattern "$dir"/*.ar with * unexpanded
        echo "This directoy is empty"
        echo "$dir"

#        ls -1 "$1" | awk -F "/|-" '{print $11 "-" $12 "-" $13 }' |

#        while read -r; do
#            echo "python2.7 "$software_path"reduce_single_station_GLOW_4files.py --stem "$REPLY" --indir "$sub_dir" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$list
#        done

    elif [ "$#" -lt 3 ]; then
        # do things when less than 3 files were found
        # the filenames are in "$@"
        echo "Less than 3 files"
        ls -1 "$@"
#        ls -1 "$@" >> /data0/abubakr/J0139+5814/less_than_three_files.txt
    elif [ "$#" -eq 3 ]; then
        echo "3 files"
        ls -1 "$@" # do things when 3 files were found
    elif [ "$#" -eq 4 ]; then
        echo "4 files"
        ls -1 "$@" # do things when 4 files were found
#        psredit -Q -q -c int[0]:mjd "$@" |
        psredit -Q -q -c int[0]:mjd "$@" |  awk  '{print substr($1,1,9)}' |

        while read -r; do
            echo "python2.7 "$software_path"reduce_single_station_GLOW_4files.py --stem "$REPLY" --indir "$sub_dir" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$list
        done




    else
        echo "More than 4 files"
        ls -1 "$@" # do things when more than 4 files were found
    fi
done



#====================================================================================================================================================================================================
#====================================================================================================================================================================================================
#dir="find /data2/lofar/LC0_014/GLOW/J0139+5814/*" #$1
#echo $dir

#subdirectories=$(find $dir -type d) # find only subdirectories in dir
#echo $subdirectories

#for subdir in $subdirectories;
#do
#   n_files=$(find $subdir -name *.ar -maxdepth 1 -type f | wc -l) # find ordinary files in subdir and get it quantity
#   echo $n_files
#   if [ $n_files -eq 4 ]
#   then
#      do_something_4
#   fi

#   if [ $n_files -eq 3 ]
#   then
#      do_something_3
#   fi
#
#   if [ $n_files -lt 3 ]
#   then
#      do_something_else
#   fi
#done 

#==========================================================================================================================

##find /data2/lofar/LC0_014/GLOW/J0139+5814/**/*.ar | while read f; do pam -pm ${f}; done;

#==========================================================================================================================
#files="find /data2/lofar/LC0_014/GLOW/J0139+5814/**/*.ar"

#for file in $files; do
#    echo "file"

#done


