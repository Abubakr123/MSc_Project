#!/usr//bin/env bash
dir="$1"
output_dir="$2"
list="$3"


st1="DE601"
st2="DE602"
st3="DE603"
st5="DE605"


# loop on all the sub-directories in the maen directories
for sub_dir in "$dir"/*; do
    # choose the file with ar.pscr extension
    set -- "$sub_dir"/*.ar.pscr
    DE601=`psredit -Q -q -c site "$1"`
    if [ $DE601 = $st1 ]; then
        ls -1 "$@"
    fi
done

