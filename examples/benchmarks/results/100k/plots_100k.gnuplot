
set autoscale
#set grid
set key right bottom
set xtic auto
set ytic auto
set datafile separator ','
set xlabel "Time (hours)"
set ylabel "Memory usage (MiB)"

set style line 1 lw 2 lc rgb "red"
set style line 2 lw 2 lc rgb "green"
set style line 3 lw 2 lc rgb "blue"

#//-------------------------------------------------------//

set title "100K files - Full build"
set key right top

set label 1 "SCons was killed during 'Reading SConscript files ...'" at 1,1300 tc rgb "dark-red"
set label 2 "Waf failed with error: 'Cannot allocate memory' while building file 9425/101000" at 1,1000 tc rgb "dark-green"
set label 3 "Aqualid successfully finished in about 9 hours" at 5,750 tc rgb "dark-blue"

set terminal png size 1024,600
set output "bench100k_full.png"
plot "mem_usage_aql_100k.txt"   using ($1/3600):($2/1024) title 'Aqualid 0.5' with lines ls 3,\
     "mem_usage_scons_100k.txt" using ($1/3600):($2/1024) title 'SCons SCons 2.3.4'   with lines ls 1,\
     "mem_usage_waf_100k.txt"   using ($1/3600):($2/1024) title 'Waf 1.8.4'     with lines ls 2

#//-------------------------------------------------------//

set grid
set title "100K files - Up to date build"
set key right bottom
set xlabel "Time (minutes)"
unset label 1
unset label 2
unset label 3

set terminal png size 1024,600
set output "bench100k_nop.png"
plot "mem_usage_aql_100k_nop.txt" using ($1/60):($2/1024) title 'Aqualid 0.5' with lines ls 3
