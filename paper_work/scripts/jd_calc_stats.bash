#!/bin/bash

# WRITTEN BY JULIAN DONNER
# LAST MODIFIED: 2019-04-15

help=false; offset=false; format='%.10e\n'; mean=false; median=false; ecol=0
for cmd in "$@"; do
    case $cmd in
        -c=*|-col=*) col="${cmd#*=}";;
        -e=*|-ecol=*) ecol="${cmd#*=}";;
	-o=*|-offset=*) offset=true; ref="${cmd#*=}";;
        -h|-help) help=true;;
        -f=*|-format=*) format="${cmd#*=}";;
        -r|-round) format='%g\n';;
	-mean) mean=true;;
	-median) median=true;;
        *) file=$cmd;;
    esac
done

test -z "$col" && col=1
if ! test -f $file; then
    echo "FILE_NOT_FOUND_$file"
    exit 1
fi

if ! $mean && ! $median; then
    mean=true
    median=true
fi

if $help; then
    echo ""
    echo "usage: $0 [options] [FILE]"
    echo ""
    echo "if no file is given, read from stdin"
    echo "options:"
    echo " -h[elp]         this help"
    echo " -f[ormat]=STR   format output according to format string STR"
    echo " -r[ound]        round output (same as -f='%g')"
    echo " -c[ol]=COL      use this column"
    echo " -e[col]=COL     use this column as uncertainty for weighting"
    echo " -o[ffset]=VAL   use absolute offset from VAL instead"
    echo " -mean           calc mean"
    echo " -median         calc median"
    echo ""
    exit 0
fi

# read in, calc offset if requested
if test $ecol -eq 0; then
    vals=$(awk '($1!~/^#/){print $c}' c=$col $file)
    $offset && vals=$(echo "$vals" | awk '{printf("%.10e\n",$1>r ? $1-r : r-$1)}' r=$ref)
else
    vals=$(awk '($1!~/^#/){print $c,$e}' c=$col e=$ecol $file)
    $offset && vals=$(echo "$vals" | awk '{printf("%.10e %.10e\n",$1>r ? $1-r : r-$1,$2)}' r=$ref)
fi

# only proceed if there is actual input, n is needed for median later
n=$(echo "$vals" | wc -l)
if test $n -eq 0; then
    echo 0
    exit
fi

# calc mean
if $mean; then
    $median && echo -n "mean:   "
    if test $ecol -eq 0; then
	echo "$vals" | awk 'BEGIN{s=0;n=0}{s+=$1;n+=1}END{printf("'$format'",s/n)}'
    else
	echo "$vals" | awk 'BEGIN{s=0;w=0}{s+=$1/$2/$2;w+=1/$2/$2}END{printf("'$format'",s/w)}'
    fi
fi
# calc median
if $median; then
    $mean && echo -n "median: "
    sorted=$(echo "$vals" | sort -g)
    if (($n%2==0)); then
	echo "$sorted" | awk 'BEGIN{s=0}(NR==n/2||NR==n/2+1){s+=$1}END{printf("'$format'",s/2)}' n=$n
    else
	echo "$sorted" | awk '(NR==(n+1)/2){printf("'$format'",$1)}' n=$n
    fi
fi
