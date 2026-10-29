set root "D:/dsh-projects/kth_fpga"

puts "== use current project/BD =="
open_bd_design [get_files system.bd]

puts "== tie gru_mv_0/ap_rst_n high =="
if {[llength [get_bd_cells -quiet const_one]] == 0} {
    create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 const_one
}
set_property -dict [list CONFIG.CONST_WIDTH {1} CONFIG.CONST_VAL {1}] [get_bd_cells const_one]

set oldnet [get_bd_nets -quiet -of_objects [get_bd_pins gru_mv_0/ap_rst_n]]
if {$oldnet ne ""} {
    disconnect_bd_net $oldnet [get_bd_pins gru_mv_0/ap_rst_n]
}
connect_bd_net [get_bd_pins const_one/dout] [get_bd_pins gru_mv_0/ap_rst_n]

validate_bd_design
save_bd_design

puts "== regenerate bitstream =="
reset_run synth_1
reset_run impl_1
launch_runs synth_1 -jobs 8
wait_on_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
puts "STATUS: [get_property STATUS [get_runs impl_1]]"

write_hw_platform -fixed -include_bit -force -file "$root/ps7020_gru.xsa"
puts "DONE $root/ps7020_gru.xsa"
