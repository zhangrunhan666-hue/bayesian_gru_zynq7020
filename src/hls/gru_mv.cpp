#include "gru_mv.h"
#include "weights_hls.h"

#include <stdint.h>

void gru_mv(const ap_uint<8> x[GRU_INPUT],
            float gi[GRU_GATES])
{
#pragma HLS INTERFACE s_axilite port=x bundle=control
#pragma HLS INTERFACE s_axilite port=gi bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

    ap_uint<8> xl[GRU_INPUT];

#pragma HLS ARRAY_PARTITION variable=xl cyclic factor=16 dim=1
#pragma HLS ARRAY_PARTITION variable=W_ih cyclic factor=16 dim=2

    for (int i = 0; i < GRU_INPUT; ++i) {
#pragma HLS PIPELINE II=1
        xl[i] = x[i];
    }

    /* gi = W_ih * (x/255) + b_ih, 16 integer MAC lanes */
    for (int o = 0; o < GRU_GATES; ++o) {
        int32_t acc[16];
#pragma HLS ARRAY_PARTITION variable=acc complete
        for (int l = 0; l < 16; ++l) {
#pragma HLS UNROLL
            acc[l] = 0;
        }
        for (int i = 0; i < GRU_INPUT; i += 16) {
#pragma HLS PIPELINE II=1
            for (int l = 0; l < 16; ++l) {
#pragma HLS UNROLL
                acc[l] += (int32_t)W_ih[o][i + l] * (int32_t)xl[i + l];
            }
        }
        for (int step = 8; step > 0; step >>= 1) {
#pragma HLS UNROLL
            for (int l = 0; l < step; ++l) {
                acc[l] += acc[l + step];
            }
        }
        int64_t sum = (int64_t)acc[0];
        gi[o] = (float)sum * W_ih_scale + (float)b_ih[o] * b_ih_scale;
    }
}
