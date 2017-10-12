#!/bin/bash
dir="*.pscr.*"

#ls -1 $dir/*.zap.* | #awk -F "." '{print $1}' |

for file in $dir 
do

        echo processing the file: "$file"
        pav -g ""$file"_avprof.ps/cps" -DFT "$file" 
        pav -g ""$file"_fprof.ps/cps" -GTd "$file" 
        pav -g ""$file"_ds.ps/cps" -j "$file" 
        pav -g ""$file"_subi.ps/cps" -R "$file" 
        pav -g ""$file"_stack.ps/cps" -YFd "$file" 

done

