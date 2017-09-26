#!/bin/bash

#check if the number of the files is equal
ls -1 *_122_133.ar | wc -l
ls -1 *_122_255.ar | wc -l
ls -1 *_122_377.ar | wc -l
ls -1 *_122_499.ar | wc -l

#creat a file list
#ls -1 *_122_133.ar > list1.txt

awk '{print substr($0, 1, length($0)-11)}' list1.txt |
while read -r; do
   echo "python2.7 reduceSingleStation_modefy.py  --stem  "$REPLY"  --indir  --outdir  --eph  --tscr  --fscr  --psrsh  --clean  --verbose">>list_of_command.txt

done
