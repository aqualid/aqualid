
set autoscale
set grid
set key right bottom
set xtic auto
set ytic auto
set datafile separator ','
set ylabel "Memory usage (MiB)"

set style line 1 lw 2 lc rgb "blue"
set style line 2 lw 2 lc rgb "cyan"
set style line 3 lw 2 lc rgb "green"
set style line 4 lw 2 lc rgb "red"
set style line 5 lw 2 lc rgb "brown"

#//-------------------------------------------------------//

set title "10000 files - Full build"
set xlabel "Time (minutes)"
set key left top

set terminal png size 1024,768
set output "bench10k_full.png"
plot "mem_usage_aql_0.6.1_all.txt" using ($1/60):($2/1024) title 'Aqualid 0.6.1' with lines ls 1,\
     "mem_usage_aql_0.6.1_all_batch.txt" using ($1/60):($2/1024) title 'Aqualid 0.6.1 (batch)' with lines ls 2,\
     "mem_usage_aql_0.5.3_all.txt" using ($1/60):($2/1024) title 'Aqualid 0.5.3' with lines ls 3,\
     "mem_usage_waf_1.8.7_all.txt" using ($1/60):($2/1024) title 'Waf 1.8.7' with lines ls 4,\
     "mem_usage_scons_2.3.4_all.txt" using ($1/60):($2/1024) title 'SCons 2.3.4' with lines ls 5,\

#//-------------------------------------------------------//

set title "10000 files - Up to date build"
set xlabel "Time (seconds)"

set terminal png size 1024,768
set output "bench10k_none.png"
plot "mem_usage_aql_0.6.1_none.txt" using 1:($2/1024) title 'Aqualid 0.6.1' with lines ls 1,\
     "mem_usage_aql_0.6.1_none_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)' with lines ls 2,\
     "mem_usage_aql_0.5.3_none.txt" using 1:($2/1024) title 'Aqualid 0.5.3' with lines ls 3,\
     "mem_usage_waf_1.8.7_none.txt" using 1:($2/1024) title 'Waf 1.8.7' with lines ls 4,\
     "mem_usage_scons_2.3.4_none.txt" using 1:($2/1024) title 'SCons 2.3.4' with lines ls 5,\

#//-------------------------------------------------------//

set title "10000 files - Incremental build"
set xlabel "Time (seconds)"

set terminal png size 1024,768
set output "bench10k_inc.png"
plot "mem_usage_aql_0.6.1_some.txt" using 1:($2/1024) title 'Aqualid 0.6.1' with lines ls 1,\
     "mem_usage_aql_0.6.1_some_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)' with lines ls 2,\
     "mem_usage_aql_0.5.3_some.txt" using 1:($2/1024) title 'Aqualid 0.5.3' with lines ls 3,\
     "mem_usage_waf_1.8.7_some.txt" using 1:($2/1024) title 'Waf 1.8.7' with lines ls 4,\
     "mem_usage_scons_2.3.4_some.txt" using 1:($2/1024) title 'SCons 2.3.4' with lines ls 5,\

#//===========================================================================//

set title "10000 files - Full build (results for different Aqualid versions)"
set xlabel "Time (minutes)"
set key right bottom

set terminal png size 1024,768
set output "bench10k_aql_full.png"
plot "mem_usage_aql_0.6.1_all.txt" using ($1/60):($2/1024) title 'Aqualid 0.6.1' with lines ls 1,\
     "mem_usage_aql_0.6.1_all_batch.txt" using ($1/60):($2/1024) title 'Aqualid 0.6.1 (batch)' with lines ls 2,\
     "mem_usage_aql_0.6.1_all_sqlite.txt" using ($1/60):($2/1024) title 'Aqualid 0.6.1 (sqlite)' with lines ls 3,\
     "mem_usage_aql_0.5.3_all.txt" using ($1/60):($2/1024) title 'Aqualid 0.5.3' with lines ls 4,\
     "mem_usage_aql_0.5.3_all_batch.txt" using ($1/60):($2/1024) title 'Aqualid 0.5.3 (batch)' with lines ls 5,\

#//-------------------------------------------------------//

set title "10000 files - Up to date build (results for different Aqualid versions)"
set xlabel "Time (seconds)"

set terminal png size 1024,768
set output "bench10k_aql_none.png"
plot "mem_usage_aql_0.6.1_none.txt" using 1:($2/1024) title 'Aqualid 0.6.1' with lines ls 1,\
     "mem_usage_aql_0.6.1_none_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)' with lines ls 2,\
     "mem_usage_aql_0.6.1_none_sqlite.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (sqlite)' with lines ls 3,\
     "mem_usage_aql_0.5.3_none.txt" using 1:($2/1024) title 'Aqualid 0.5.3' with lines ls 4,\
     "mem_usage_aql_0.5.3_none_batch.txt" using 1:($2/1024) title 'Aqualid 0.5.3 (batch)' with lines ls 5,\

#//-------------------------------------------------------//

set title "10000 files - Incremental build (results for different Aqualid versions)"
set xlabel "Time (seconds)"

set terminal png size 1024,768
set output "bench10k_aql_inc.png"
plot "mem_usage_aql_0.6.1_some.txt" using 1:($2/1024) title 'Aqualid 0.6.1' with lines ls 1,\
     "mem_usage_aql_0.6.1_some_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)' with lines ls 2,\
     "mem_usage_aql_0.6.1_some_sqlite.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (sqlite)' with lines ls 3,\
     "mem_usage_aql_0.5.3_some.txt" using 1:($2/1024) title 'Aqualid 0.5.3' with lines ls 4,\
     "mem_usage_aql_0.5.3_some_batch.txt" using 1:($2/1024) title 'Aqualid 0.5.3 (batch)' with lines ls 5,\

