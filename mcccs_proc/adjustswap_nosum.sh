#!/bin/bash

outfile=$1/run1a.dat
if [ $# -gt 1 ]; then
	ncacc=$2
else
	ncacc=1
fi

if [ $# -gt 2 ]; then
    maxprob=$3
else
    maxprob=0.5
fi


match=( $(grep "pmvol" $outfile) )
pmvol=${match[1]}
match=( $(grep "pmswap" $outfile) )
pmswap=${match[1]}
match=( $(grep "pmcb" $outfile) )
pmcb=${match[1]}
match=( $(grep "pmtra" $outfile) )
pmtrans=${match[1]}

match=( $(grep "number of boxes" $outfile) )
nboxes=${match[6]}
#match=( $(grep "number of cycles" $outfile) )
match=( $(wc -l $1/fort.12) )
let "ncycles=(${match[0]}-1)/$nboxes"
swaps=0
match=( $(grep "accepted = " $outfile) )
for i in `seq 1 $nboxes`; do
	let swaps=$swaps+${match[17*$i-1]}
done
if [ $swaps == 0 ]; then
    swaps=1
fi
newswap=$(python -c "print(format(min($pmswap*$ncycles/$swaps/$ncacc, $maxprob), '.5f'))")
newcb=$(python -c "print(format((1-$newswap)*($pmcb-$pmswap)/(1-$pmswap) , '.5f'))")
newtrans=$(python -c "print(format((1-$newswap)*($pmtrans-$pmcb)/(1-$pmswap) , '.5f'))")
echo $newswap $newcb $newtrans

