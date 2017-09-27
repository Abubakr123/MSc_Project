#!/bin/bash


#creat a list of command lines 
ls -1 *_122_133.ar | awk '{print substr($0, 1, length($0)-11)}'|
while read -r; do
   echo "python2.7 reduceSingleStation_modefy.py  --stem  "$REPLY"  --indir  --outdir  --eph  --tscr  --fscr  --psrsh  --clean  --verbose">>list_of_command.txt

done


