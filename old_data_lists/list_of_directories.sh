#!/bin/bash

path=/data0/abubakr/
psr=ls -1 $path |

#Create the list of command lines
while read -r; do
  echo "bash initial_par_F8T10_iniDM.sh $REPLY" >> pulsar_list.txt

done
