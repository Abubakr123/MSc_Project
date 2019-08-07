#!/bin/sh
# bash ~/MSc_Project/paper_work/rename_pulsar_file.sh 's/^J1115+5030/B1112+50/' files_to-be-renamed

e=$1
shift

for f in $*; do
    fNew=$(echo "$f" | sed "$e")
    mv "$f" "$fNew";
done
