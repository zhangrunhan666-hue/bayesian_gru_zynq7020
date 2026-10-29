open_project -reset gru_mv
set_top gru_mv
add_files gru_mv.cpp
add_files -tb gru_mv_tb.cpp

open_solution -reset solution1 -flow_target vivado
set_part xc7z020clg400-2
create_clock -period 10 -name default

csim_design
csynth_design
export_design -format ip_catalog -output ./gru_mv_ip

exit
