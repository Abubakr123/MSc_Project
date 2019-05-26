#!/bin/bash

# WRITTEN BY JULIAN DONNER
# LAST MODIFIED: 2019-04-16

# EXITCODES:
# 1 - invalid arguments / script setup
# 2 - too few ToAs
# 3 - tempo2 crashed
# 4 - final rms bad
# 5 - medoff/P0 large
# 6 - chisq too large [disabled]
# 7 - unknown tempo2 problem
# 8 - DMunc too large
# 9 - final rms / P0 large
function end_script { # exitcode msg
    echo "$2"
    exit $1
}

#
# check requirements
#
scrdir=$(dirname $(readlink -f $0))
source $scrdir/jd_funcs.bash
calc_stats=$scrdir/jd_calc_stats.bash
require_script $calc_stats

#
# setup variables and read command line
#
unc_cutoff=3
res_cutoff_mean=3
res_cutoff_median=3
rms_over_medunc_threshold=20 # some pulsars have significant structure in residuals
rms_over_P0_threshold=0.15

avg_mode="mean"
help=false; verbose=false; vv=false; norescale=false; debug=false
par=""; tim=""; fmin=0; fmax=100000; initDM=""; plot_out=""; ignore_thresh=1e+06; resfile=""
outlier_rejection=false; unc_rejection=false; rms_rejection=false; chisq_threshold=1e+06
for cmd in "$@"; do
    case $cmd in
        -p=*) par=$(fix_path "${cmd#*=}");;
        -t=*) tim=$(fix_path "${cmd#*=}");;
	-fmin=*) fmin="${cmd#*=}";;
	-fmax=*) fmax="${cmd#*=}";;
	-i=*) initDM="${cmd#*=}";;
	-equad=*) equad_str="EQUAD ${cmd#*=}";;
	-o=*) plot_out=$(fix_path "${cmd#*=}");;
	-n|-norescale) norescale=true;;
	-h) help=true; verbose=true;;
	-v) verbose=true;;
	-vv) verbose=true; vv=true;;
	-d|-debug) debug=true;;
	-r=*|-res=*) resfile=$(fix_path "${cmd#*=}");;
	-O) outlier_rejection=true;;
	-m|-median) avg_mode="median";;
	-U) unc_rejection=true;;
	-R) rms_rejection=true;;
	-C=*) chisq_threshold="${cmd#*=}";;
	-I=*) ignore_thresh="${cmd#*=}";;
        *) echo "invalid option '$cmd'!"; help=true;;
    esac
done

[[ "$avg_mode" == "mean" ]] && res_cutoff=$res_cutoff_mean || res_cutoff=$res_cutoff_median

! test -f $par && echo "invalid parfile!" && help=true
! test -f $tim && echo "invalid timfile!" && help=true
if $help
then
    $verbose && echo
    $verbose && echo "usage: $0 [options]"
    $verbose && echo
    $verbose && echo " -h            this help"
    $verbose && echo " -v            verbose output, plot residuals"
    $verbose && echo " -vv           very verbose: plot residuals after each step"
    $verbose && echo " -d[ebug]      print a _lot_ for debugging"
    $verbose && echo " -p=PARFILE    use this parfile (required)"
    $verbose && echo " -t=TIMFILE    use this timfile (required)"
    $verbose && echo " -fmin=VAL     only consider frequencies > VAL"
    $verbose && echo " -fmax=VAL     only consider frequencies <= VAL"
    $verbose && echo " -i=VAL        use VAL as initial DM value for fit"
    $verbose && echo " -equad=VAL    use EQUAD value VAL (in us)"
    $verbose && echo " -n[orescale]  do not multiply DM uncertainty by"
    $verbose && echo "               sqrt(red.chisq) if red.chisq is less than 1"
    $verbose && echo " -o=FILE       plot final result to FILE (format is eps)"
    $verbose && echo " -r[es]=FILE   print final residuals to FILE"
    $verbose && echo
    $verbose && echo " -O            reject outlier ToAs"
    $verbose && echo " -m[edian]      use median offset rejection instead of mean"
    $verbose && echo " -U            reject high uncertainty ToAs"
    $verbose && echo " -R            reject DM measurement if the post-fit RMS is bad"
    $verbose && echo " -C=VAL        reject DM measurement if the fit chisq is above VAL"
    $verbose && echo " -I=VAL        reject DM measurement if it's uncertainty is above VAL"
    $verbose && echo
    exit 1
fi

# funcs
function check_for_enough_toas {
    test $ntoa -lt 4 && end_script 2 "CALCDM_TOO_FEW_TOAS"
}
function build_tim {
    echo -e "FORMAT 1\nMODE 1\n$equad_str" > $temptim; echo "$timc" >> $temptim
    ntoa=$(echo "$timc" | wc -l)
}
function get_tempo2_npsrnobs {
    tempo2_nobs=$(($(echo "$timc" | wc -l) + 3))
    test $tempo2_nobs -gt 1000 && echo "-npsr 1 -nobs $tempo2_nobs"
}
function calc_residuals {
    res=$(tempo2 -output general2 -f $temppar $temptim -s "{freq} {pre} {err}\n" -nofit \
	$(get_tempo2_npsrnobs) | \
	awk 'BEGIN{x=0}{if($1=="Finished") x=0; if(x) print; if($1=="Starting") x=1;}')
    $debug && echo "copying par and tim to ~/debug.???"
    $debug && cp $temppar ~/debug.par && cp $temptim ~/debug.tim
    $debug && echo "RESIDUALS tail" && echo "#############" && echo "$res" | tail
}
function get_res_stats {
    calc_residuals
    $verbose && echo ""
    mres=$(echo "$res" | $calc_stats -$avg_mode -r -c=2 -e=3)
    moff=$(echo "$res" | $calc_stats -$avg_mode -r -c=2 -e=3 -o=$mres)
    $verbose && echo "$avg_mode residual: $mres"
    $verbose && echo -n "$avg_mode offset: $moff sec, i.e. "
    $verbose && echo $moff $P0 | awk '{printf("%f",$1/$2)}'
    $verbose && echo " pulse periods"
}
function res_rejection {
    # relative residual cutoff is either mreloff*preset_cutoff, or at least the preset
    mreloff=$(echo "$res" | awk '{print $2/$3/1e-06}' | $calc_stats -r -$avg_mode -o=0)
    $verbose && echo "$avg_mode residual: $mreloff sigmas"
    cutoff=$(echo $mreloff | awk '{if ($1>1) print c*$1; else print c}' c=$res_cutoff)
    $verbose && echo "residual cutoff: $cutoff sigmas"

    timc_res=$(paste <(echo "$timc") <(echo "$res" | awk '{print $2}'))
    timc=$(echo "$timc_res" | awk '{o=($NF-m)/$4/1e-06; if(o<c && -o<c) {$NF=""; print}}' \
	m=$mres c=$cutoff)

    build_tim
    $verbose && echo "number of ToAs after res_rejection: $ntoa"
    check_for_enough_toas
}
function DM_fit {
    $verbose && echo "" && echo "fitting for DM..."
    tempo2 -f $temppar $temptim -nofit -fit DM -newpar $(get_tempo2_npsrnobs) &> /dev/null
    ! test -f new.par && end_script 3 "CALCDM_TEMPO2_FAILED"
    awk '($1=="START"){$2-=1}($1=="FINISH"){$2+=1} 1' new.par > $temppar
}
function significant_outliers { # significance_level
    # calculate largest jump (in simgas) between 2 residuals
    worst=$(echo "$res" | sort -gk1 | \
	awk 'BEGIN{max=0;prev=0} \
             (prev!=0){d=1e+06*($2-prev)/sqrt($3*$3+sprev*sprev); d=d>0?d:-d; if (d>max) max=d} \
             {prev=$2;sprev=$3} \
             END{print max}')
    $verbose && echo "most significant jump between 2 ToAs: $worst sigmas (checking $1)"
    echo $worst $1 | awk '($1>$2){exit 1}'
}
function moff_over_P0_large {
    echo $moff $P0 | awk '($1/$2<0.1){exit 1}'
}
function rms_over_P0_large {
    rms=$(echo "$res" | awk 'BEGIN{sum=0;n=0}{n++;sum+=$2*$2}END{print sqrt(sum/n)}')
    $verbose && echo -en "\nrms/P0 = "
    $verbose && echo -n $(echo $rms $P0 | awk '{print $1/$2}')
    $verbose && echo " (threshold $rms_over_P0_threshold)"
    echo $rms $P0 $rms_over_P0_threshold | awk '($1/$2<$3){exit 1}'
}
function rms_ok {
    rms=$(echo "$res" | awk 'BEGIN{sum=0;n=0}{n++;sum+=$2*$2}END{print sqrt(sum/n)}')
    $verbose && echo -en "\nrms/medunc = "
    $verbose && echo -n $(echo $rms $medunc | awk '{print $1/(1e-06*$2)}')
    $verbose && echo " (threshold $rms_over_medunc_threshold)"
    echo $rms $medunc $rms_over_medunc_threshold | awk '($1/(1e-06*$2)>$3){exit 1}'
}
function plot { # title
    [[ $1 == "post-fit" ]] && final=true || final=false
    $vv || ($final && ($verbose || ! test -z "$plot_out")) || return

    if test -z "$plot_title"; then
	plot_file=$(echo "$timc" | tail -1 | awk '{print $1}')
	plot_mjd=${plot_file##*/}; plot_mjd=${plot_mjd%%.*}
	[[ "$plot_file" =~ [BJ][0-9]{4}[+-][0-9]{2,4} ]] && plot_psr_str=" for PSR $BASH_REMATCH"
	plot_title="residuals$plot_psr_str on MJD $plot_mjd"
    fi

    calc_residuals # else this plots residuals from last step ...
    echo "$res" > res.dat
    echo "set term post col eps enhanced 'Helvetica,18'" > temp.plt
    echo "set out 'temp.eps'" >> temp.plt
    echo "set grid" >> temp.plt
    echo "set title '$1 $plot_title'" >> temp.plt
    echo "set xlabel 'frequency (MHz)'" >> temp.plt
    echo "set ylabel 'residuals ({/Symbol m}s)'" >> temp.plt
    echo 'plot "res.dat" u 1:($2*1e+06):3 w ye lw 2.5 lc rgb "blue" notitle' >> temp.plt

    gnuplot temp.plt &> /dev/null
    $verbose && gv --scale=3 temp.eps
    $final && ! test -z "$plot_out" && cp temp.eps $plot_out
}
function read_p0 { # parfile
    if test $(grep -w P0 $par | wc -l) -eq 1; then
	grep -w P0 $par | awk '{print $2}'
    else
	grep -w F0 $par | awk '{print 1/$2}'
    fi
}
function unc_rejection {
    if [[ "$medunc" == "0" ]]; then
        # weird tempo2 error (happened once with -nobs 30, but not with different number)
	# doesn't crash with error code
	end_script 7 "CALCDM_UNKNOWN_TEMPO2_PROBLEM"
    fi
    timc=$(echo "$timc" | awk '($4!=0 && $4<c*m)' m=$medunc c=$unc_cutoff)
    build_tim
    $verbose && echo "number of ToAs after unc rejection: $ntoa"
    plot "unc-rejected"
}

# exit trap
function cleanup {
    rm -r $tempdir
}
tempdir=$(mktemp -d -t $(basename $0).XXXXXXXXXX)
trap cleanup EXIT

############
### init ###
############
temptim=$tempdir/temp.tim
temppar=$tempdir/temp.par
# adjust parfile
awk '($1=="START"){$2=56000} ($1=="FINISH"){$2=60000} 1' $par > $temppar
# if inital DM is given, update in parfile
if test -n "$initDM"
then
    awk '($1=="DM"){$2=i} 1' i=$initDM $temppar > $temppar.up && mv $temppar.up $temppar
fi
# read timfile and cut ToAs outside of frequency range
timc=$(cat $tim | awk '$1!~/^C|MODE|FORMAT/ && $2>min && $2<=max' min=$fmin max=$fmax)
build_tim
# read out P0
P0=$(read_p0)

cd $tempdir
$verbose && echo ""
$verbose && echo "total number of ToAs: $ntoa"
plot "initial"
medunc=$(echo "$timc" | $calc_stats -median -c=4)
$verbose && echo "median ToA uncertainty: $medunc us"
$unc_rejection && unc_rejection

check_for_enough_toas

if $outlier_rejection
then
    iter=1
    while true
    do
	ntoa_old=$ntoa
        # residual stats
	get_res_stats
        # reject by residual
        # - in first step only if median residual is good, otherwise there might be a huge slope
	test $iter -gt 1 || ! moff_over_P0_large && res_rejection
        # break if no ToAs get removed and fit for DM already
	test $ntoa -eq $ntoa_old && test $iter -gt 1 && break
        # end script if median offset is bad after second iteration
	test $iter -gt 1 && moff_over_P0_large && end_script 5 "CALCDM_MOFF/P0_LARGE"
        # fit for DM
	DM_fit
	plot "intermediate-${iter}-post-fit"
	((iter++))
    done
else
    DM_fit
    get_res_stats
    moff_over_P0_large && end_script 5 "CALCDM_MOFF/P0_LARGE"
fi

# check if rms is ok in final residuals
! $rms_rejection || rms_ok || end_script 4 "CALCDM_RMS_BAD"
$rms_rejection && rms_over_P0_large && end_script 9 "CALCDM_RMS_OVER_P0_LARGE"

# read results
dm=$(grep -w DM $temppar | awk '{print $2,$4}')
ntoa=$(echo "$timc" | wc -l)
chisq=$(grep -w CHI2R $temppar | awk '{print $2}')
tel=$(echo "$timc" | tail -1 | awk '{print $5}')
if $norescale
then
    # undo the multi by sqrt(red.chisq) that cannot be turned off in tempo2
    dm=$(echo "$dm $chisq" | awk '{if ($3<1) print $1,$2/sqrt($3); else print $1,$2}')
fi
# reject because of high chisq
! echo $chisq $chisq_threshold | awk '($1>$2){exit 1}' && end_script 6 "CALCDM_CHI2R_HUGE"
# reject because of high uncertainty
echo $dm $ignore_thresh | awk '($2>$3){exit 1}' || end_script 8 "CALCDM_DMUNC_HUGE"

# print
$verbose && echo -e "\nDM DMunc nToA chisq TEL"
echo "$dm $ntoa $chisq $tel"

# print residuals to file if requested
test -n "$resfile" && echo "$res" > $resfile

# plot
plot "post-fit"

exit 0