# HLS Source Notes

- `gru_mv.cpp` / `gru_mv.h`: W_ih × x + b_ih kernel, 16 parallel int32 MAC lanes.
- `weights_hls.h`: Jester 3-class full model W_ih/b_ih, int16.
- `gru_mv_tb.cpp` + `tb_data.h`: C testbench. `tb_data.h` is generated from Jester validation clip 0, frame 1, with `TB_GI` equal to the HLS raw output (HLS does not divide by 255; PS applies the normalization correction).
- `gru_mv_csim.cfg`: config for `vitis-run --mode hls --csim`; if the CLI stalls, run **C SIMULATION** in the Vitis HLS GUI.
- `run_hls.tcl`: legacy script; it still includes `csim_design`, so the testbench must match `weights_hls.h`.
