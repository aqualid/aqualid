
set autoscale
set grid
set key right bottom
set xtic auto
set ytic auto
set datafile separator ','
set xlabel "Time (seconds)"
set ylabel "Memory usage (MiB)"

set style line 1 lw 2 lc rgb "red"
set style line 2 lw 2 lc rgb "green"
set style line 3 lw 2 lc rgb "blue"
set style line 4 lw 2 lc rgb "brown"
set style line 5 lw 2 lc rgb "orange"

#//-------------------------------------------------------//

set title "1000 files - Full build"

# mem_usage_aql_0.6.1_full.txt
# mem_usage_aql_0.6.1_no.txt
# mem_usage_aql_0.6.1_partial.txt
# mem_usage_aql_0.6.1_sql_full.txt
# mem_usage_aql_0.6.1_sql_no.txt
# mem_usage_aql_0.6.1_sql_partial.txt

set terminal png size 1024,600
set output "bench1k_full.png"
plot "mem_usage_aql_0.6.1_full.txt" using 1:($2/1024) title 'Aqualid 0.6.1'   with lines ls 1,\
     "mem_usage_aql_0.6.1_full_sql.txt" using 1:($2/1024) title 'Aqualid 0.6.1(use_sqlite3)'   with lines ls 2,\
     "mem_usage_aql_0.6.1_full_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)'   with lines ls 3,\
     "mem_usage_aql_0.6.1_full_sql_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (use_sqlite3,batch)'   with lines ls 4,\
     "mem_usage_aql_0.5.3_full.txt" using 1:($2/1024) title 'Aqualid 0.5.3'   with lines ls 5,\

#//-------------------------------------------------------//

set title "1000 files - No build"

set terminal png size 1024,600
set output "bench1k_nop.png"
plot "mem_usage_aql_0.6.1_no.txt" using 1:($2/1024) title 'Aqualid 0.6.1'   with lines ls 1,\
     "mem_usage_aql_0.6.1_no_sql.txt" using 1:($2/1024) title 'Aqualid 0.6.1(use_sqlite3)'   with lines ls 2,\
     "mem_usage_aql_0.6.1_no_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)'   with lines ls 3,\
     "mem_usage_aql_0.6.1_no_sql_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (use_sqlite3,batch)'   with lines ls 4,\
     "mem_usage_aql_0.5.3_no.txt" using 1:($2/1024) title 'Aqualid 0.5.3'   with lines ls 5,\

#//-------------------------------------------------------//

set title "1000 files - Partial build"

set terminal png size 1024,600
set output "bench1k_partial.png"
plot "mem_usage_aql_0.6.1_partial.txt" using 1:($2/1024) title 'Aqualid 0.6.1'   with lines ls 1,\
     "mem_usage_aql_0.6.1_partial_sql.txt" using 1:($2/1024) title 'Aqualid 0.6.1(use_sqlite3)'   with lines ls 2,\
     "mem_usage_aql_0.6.1_partial_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)'   with lines ls 3,\
     "mem_usage_aql_0.6.1_partial_sql_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (use_sqlite3,batch)'   with lines ls 4,\
     "mem_usage_aql_0.5.3_partial.txt" using 1:($2/1024) title 'Aqualid 0.5.3'   with lines ls 5,\

#//-------------------------------------------------------//

set title "1000 files - Full build"

set terminal png size 1024,600
set output "bench1k_waf_scons_aql_full.png"
plot "mem_usage_scons_2.3.4_full.txt" using 1:($2/1024) title 'SCons 2.3.4'   with lines ls 1,\
     "mem_usage_waf_1.8.7_full.txt" using 1:($2/1024) title 'Waf 1.8.7'   with lines ls 2,\
     "mem_usage_aql_0.6.1_full.txt" using 1:($2/1024) title 'Aqualid 0.6.1'   with lines ls 3,\
     "mem_usage_aql_0.6.1_full_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)'   with lines ls 4,\


#//-------------------------------------------------------//

set title "1000 files - No build"

set terminal png size 1024,600
set output "bench1k_waf_scons_aql_no.png"
plot "mem_usage_scons_2.3.4_no.txt" using 1:($2/1024) title 'SCons 2.3.4'   with lines ls 1,\
     "mem_usage_waf_1.8.7_no.txt" using 1:($2/1024) title 'Waf 1.8.7'   with lines ls 2,\
     "mem_usage_aql_0.6.1_no.txt" using 1:($2/1024) title 'Aqualid 0.6.1'   with lines ls 3,\
     "mem_usage_aql_0.6.1_no_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)'   with lines ls 4,\


#//-------------------------------------------------------//

set title "1000 files - Partial build"

set terminal png size 1024,600
set output "bench1k_waf_scons_aql_partial.png"
plot "mem_usage_scons_2.3.4_partial.txt" using 1:($2/1024) title 'SCons 2.3.4'   with lines ls 1,\
     "mem_usage_waf_1.8.7_partial.txt" using 1:($2/1024) title 'Waf 1.8.7'   with lines ls 2,\
     "mem_usage_aql_0.6.1_partial.txt" using 1:($2/1024) title 'Aqualid 0.6.1'   with lines ls 3,\
     "mem_usage_aql_0.6.1_partial_batch.txt" using 1:($2/1024) title 'Aqualid 0.6.1 (batch)'   with lines ls 4,\


