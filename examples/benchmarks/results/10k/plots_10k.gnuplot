
set autoscale
set grid
set key right bottom
set xtic auto
set ytic auto
set datafile separator ','
set xlabel "Time (minutes)"
set ylabel "Memory usage (MiB)"

set style line 1 lw 2 lc rgb "red"
set style line 2 lw 2 lc rgb "green"
set style line 3 lw 2 lc rgb "blue"
set style line 4 lw 2 lc rgb "brown"

#//-------------------------------------------------------//

set title "10000 files - Full build"
set key left top

set terminal png size 1024,600
set output "bench10k_full.png"
plot "mem_usage_scons_10k.txt" using ($1/60):($2/1024) title 'SCons 2.3.4'   with lines ls 1,\
     "mem_usage_scons_ex_10k.txt" using ($1/60):($2/1024) title 'SCons 2.3.4 (__slots__ optimizations)'   with lines ls 4,\
     "mem_usage_waf_10k.txt"   using ($1/60):($2/1024) title 'Waf 1.8.4'     with lines ls 2,\
     "mem_usage_aql_0.6_10k.txt"   using ($1/60):($2/1024) title 'Aqualid 0.6' with lines ls 3

#//-------------------------------------------------------//

set title "10000 files - Up to date build"
set xlabel "Time (seconds)"

set terminal png size 1024,600
set output "bench10k_nop.png"
plot "mem_usage_scons_10k-nop.txt" using 1:($2/1024) title 'SCons 2.3.4'   with lines ls 1,\
     "mem_usage_scons_ex_10k-nop.txt" using 1:($2/1024) title 'SCons 2.3.4 (__slots__ optimizations)'   with lines ls 4,\
     "mem_usage_waf_10k_nop.txt"   using 1:($2/1024) title 'Waf 1.8.4'     with lines ls 2,\
     "mem_usage_aql_0.6_10k_nop.txt"   using 1:($2/1024) title 'Aqualid 0.6' with lines ls 3

#//-------------------------------------------------------//

set title "10000 files - Full build - Different Aqualid versions"
set key left top

set terminal png size 1024,600
set output "bench10k_aql_full.png"
plot "mem_usage_aql_10k.txt"   using ($1/60):($2/1024) title 'Aqualid 0.5' with lines ls 1,\
     "mem_usage_aql_0.6_10k.txt"   using ($1/60):($2/1024) title 'Aqualid 0.6' with lines ls 3,\
     "mem_usage_aql_sqlite_10k.txt"   using ($1/60):($2/1024) title 'Aqualid 0.6 (use_sqlite3)' with lines ls 4

#//-------------------------------------------------------//

set title "10000 files - Up to date build - Different Aqualid versions"
set xlabel "Time (seconds)"

set terminal png size 1024,600
set output "bench10k_aql_nop.png"
plot "mem_usage_aql_10k_nop.txt"   using 1:($2/1024) title 'Aqualid 0.5' with lines ls 1,\
     "mem_usage_aql_0.6_10k_nop.txt"   using 1:($2/1024) title 'Aqualid 0.6' with lines ls 3,\
     "mem_usage_aql_sqlite_10k_nop.txt"   using 1:($2/1024) title 'Aqualid 0.6 (use_sqlite3)' with lines ls 4
