set root "D:/dsh-projects/kth_fpga"
set repo "$root/vitis_ws/gru_mv_hls/gru_mv/hls/impl/ip"
set xpr  "$root/ps7020/ps7020.xpr"

puts "== open project =="
open_project $xpr

puts "== add HLS IP repo =="
set_property ip_repo_paths [list $repo] [current_project]
update_ip_catalog -rebuild

puts "== open block design =="
open_bd_design [get_files system.bd]

puts "== enable PS M_AXI_GP0 =="
set ps [get_bd_cells ps7_0]
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 {1}] $ps

puts "== create interconnect and GRU IP =="
if {[llength [get_bd_cells -quiet axi_interconnect_0]] == 0} {
    create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 axi_interconnect_0
}
set_property -dict [list CONFIG.NUM_MI {1}] [get_bd_cells axi_interconnect_0]

if {[llength [get_bd_cells -quiet gru_mv_0]] == 0} {
    create_bd_cell -type ip -vlnv xilinx.com:hls:gru_mv:1.0 gru_mv_0
}

puts "== connect AXI =="
connect_bd_intf_net [get_bd_intf_pins ps7_0/M_AXI_GP0] [get_bd_intf_pins axi_interconnect_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M00_AXI] [get_bd_intf_pins gru_mv_0/s_axi_control]

puts "== connect clocks/resets =="
foreach p {ACLK S00_ACLK M00_ACLK} {
    connect_bd_net [get_bd_pins ps7_0/FCLK_CLK0] [get_bd_pins axi_interconnect_0/$p]
}
connect_bd_net [get_bd_pins ps7_0/FCLK_CLK0] [get_bd_pins ps7_0/M_AXI_GP0_ACLK]
connect_bd_net [get_bd_pins ps7_0/FCLK_CLK0] [get_bd_pins gru_mv_0/ap_clk]

foreach p {ARESETN S00_ARESETN M00_ARESETN} {
    connect_bd_net [get_bd_pins ps7_0/FCLK_RESET0_N] [get_bd_pins axi_interconnect_0/$p]
}
if {[llength [get_bd_cells -quiet const_one]] == 0} {
    create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 const_one
    set_property -dict [list CONFIG.CONST_WIDTH {1} CONFIG.CONST_VAL {1}] [get_bd_cells const_one]
}
connect_bd_net [get_bd_pins const_one/dout] [get_bd_pins gru_mv_0/ap_rst_n]

puts "== assign address 0x43C00000 =="
assign_bd_address -target_address_space [get_bd_addr_spaces ps7_0/Data] [get_bd_addr_segs gru_mv_0/s_axi_control/Reg] -force

puts "== validate/save =="
validate_bd_design
save_bd_design

puts "== regenerate wrapper =="
set wrapper [make_wrapper -files [get_files system.bd] -top]
add_files -norecurse -force $wrapper
set_property top system_wrapper [current_fileset]
update_compile_order -fileset sources_1

puts "== run implementation =="
reset_run synth_1
reset_run impl_1
launch_runs synth_1 -jobs 8
wait_on_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
set st [get_property STATUS [get_runs impl_1]]
puts "impl status: $st"
if {[string first "write_bitstream Complete" $st] < 0} {
    puts "ERROR: implementation did not finish"
    exit 1
}

puts "== export XSA =="
write_hw_platform -fixed -include_bit -force -file "$root/ps7020_gru_jester.xsa"
puts "DONE: $root/ps7020_gru_jester.xsa"
exit
