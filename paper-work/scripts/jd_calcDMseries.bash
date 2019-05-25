#!/bin/bash

# WRITTEN BY JULIAN DONNER
# LAST MODIFIED: 2019-04-16

#
# check requirements
#
scrdir=$(dirname $(readlink -f $0))
source $scrdir/jd_funcs.bash
calcDM=$scrdir/jd_calcDM.bash
calc_stats=$scrdir/jd_calc_stats.bash
require_script $calcDM
require_script $calc_stats

#
# read command line, setup variables and check input
#
help=false; verbose=false
par=""; tim=""; fmin=0; fmax=100000; initDMstr=; calcDM_args=""
max_gap=0.05
max_length=1
for cmd in "$@"; do
    case $cmd in
        -p=*) par=$(fix_path "${cmd#*=}");;
        -t=*) tim=$(fix_path "${cmd#*=}");;
	-i=*) initDMstr="-i=${cmd#*=}";;
	-g=*) max_gap="${cmd#*=}";;
	-m=*) max_length="${cmd#*=}";;
	-h) help=true; verbose=true;;
	-v) verbose=true;;
	-a=*) calcDM_args="${cmd#*=}";;
        *) echo "invalid option $cmd!"; help=true;;
    esac
done


if test -z "$par" || ! test -f $par || test -z "$tim" || ! test -f $tim
then
    echo "require valid .par and .tim files to calculate the DM time series!"
    help=true
fi
if $help; then
    $verbose && echo
    $verbose && echo "usage: $0 [options]"
    $verbose && echo
    $verbose && echo " -h            this help"
    $verbose && echo " -v            verbose output, plot residuals"
    $verbose && echo " -p=PARFILE    use this parfile (required)"
    $verbose && echo " -t=TIMFILE    use this timfile (required)"
    $verbose && echo " -g=VAL        set maximum gap between connected ToAs to VAL days"
    $verbose && echo " -m=VAL        set maximum total length of connected ToAs to VAL days"
    $verbose && echo " -i=VAL        use VAL as initial DM value for first fit and"
    $verbose && echo "                 the result of each fit as initial value for the next fit"
    $verbose && echo
    $verbose && echo " -a=\"ARGS\"     apply extra options to jd_calcDM.bash, e.g. ToA rejections"
    $verbose && echo "                sensible are: -O, -m, -U, -R, -C, -I, -equad, -n, -fmin, -fmax"
    $verbose && echo
    exit 1
fi

# exit trap
function cleanup {
    rm -r $tempdir
}
tempdir=$(mktemp -d -t $(basename $0).XXXXXXXXXX)
trap cleanup EXIT

# CALC DM TIME SERIES
echo "#_MJD RANGE DM DMunc nToA chisq"
grep -v -E "FORMAT|MODE|^C" $tim | sort -gk3 > $tempdir/full.tim
first=0
lines=$(wc -l $tempdir/full.tim | awk '{print $1}')
for((line=1;line<=$lines;line++)); do
    lc=$(head -$line $tempdir/full.tim | tail -1)
    mjd=$(echo $lc | awk '{print $3}')
    if [[ "$first" == "0" ]]
    then
	first=$mjd
	last=$mjd
	echo "FORMAT 1" > $tempdir/cur.tim
	echo $lc >> $tempdir/cur.tim
    elif awk 'BEGIN{if ('$mjd'>'$last'+'$max_gap' || '$mjd'>'$first'+'$max_length') exit 1}' && \
	[[ $line != $lines ]]
    then
	last=$mjd
	echo $lc >> $tempdir/cur.tim
    else
	out=$($scrdir/jd_calcDM.bash -p=$par -t=$tempdir/cur.tim $calcDM_args $initDMstr)
	if test $? == 0
	then
	    # cut away telescope identifier, because there could be multiple telescopes involved
	    out=$(echo $out | awk '{$NF=""; print}')
	    mjd=$(awk 'BEGIN{printf("%.10f",('$last'+'$first')/2)}')
	    range=$(awk 'BEGIN{print ('$last'-'$first')/2}')
	    echo $mjd $range "$out"
	    test -n "$initDMstr" && initDMstr=$(echo $out | awk '{print "-i="$1}')
	else
	    echo "problem for MJD range $last - $mjd: $out" 1>&2
	fi
	first=0
	[[ $line != $lines ]] && ((line--))
    fi
done