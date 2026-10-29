# Replace gru_mv_0 with the new Jester HLS IP and rebuild the bitstream.
# Run from Vivado Tcl Console with the ps7020 project open.

set root "D:/dsh-projects/kth_fpga"
set ipdir "$root/vitis_ws/gru_mv_hls/gru_mv/hls/impl/ip"

puts "== open block design =="
open_bd_design [get_files system.bd]

puts "== refresh IP catalog =="
set_property ip_repo_paths [list $ipdir] [current_project]
update_ip_catalog -rebuild

puts "== delete old gru_mv_0 =="
if {[llength [get_bd_cells -quiet gru_mv_0]] > 0} {
    delete_bd_objs [get_bd_cells gru_mv_0]
}

puts "== add Jester gru_mv =="
create_bd_cell -type ip -vlnv xilinx.com:hls:gru_mv:1.0 gru_mv_0

puts "== connect AXI-Lite =="
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M00_AXI] [get_bd_intf_pins gru_mv_0/s_axi_control]

puts "== connect clock/reset =="
connect_bd_net [get_bd_pins ps7_0/FCLK_CLK0] [get_bd_pins gru_mv_0/ap_clk]
if {[llength [get_bd_cells -quiet const_one]] > 0} {
    connect_bd_net [get_bd_pins const_one/dout] [get_bd_pins gru_mv_0/ap_rst_n]
} else {
    connect_bd_net [get_bd_pins ps7_0/FCLK_RESET0_N] [get_bd_pins gru_mv_0/ap_rst_n]
}

puts "== assign address =="
assign_bd_address -offset 0x43C00000 -target_address_space [get_bd_addr_spaces ps7_0/Data] [get_bd_addr_segs gru_mv_0/s_axi_control/Reg] -force

puts "== validate/save =="
validate_bd_design
save_bd_design

puts "== regenerate wrapper =="
set wrapper [make_wrapper -files [get_files system.bd] -top]
add_files -norecurse -force $wrapper
set_property top system_wrapper [current_fileset]
update_compile_order -fileset sources_1

puts "== reset and rerun synth/impl =="
reset_run synth_1
reset_run impl_1
launch_runs synth_1 -jobs 8
wait_on_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
set st [get_property STATUS [get_runs impl_1]]
puts "impl status: $st"
if {[string first "write_bitstream Complete" $st] < 0} {
    error "ERROR: implementation did not finish"
}

puts "== export Jester XSA =="
write_hw_platform -fixed -include_bit -force -file "$root/ps7020_gru_jester.xsa"
puts "DONE: $root/ps7020_gru_jester.xsa"
