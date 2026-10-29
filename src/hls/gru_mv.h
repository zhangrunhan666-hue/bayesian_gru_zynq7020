#ifndef GRU_MV_H
#define GRU_MV_H

#include <ap_int.h>

#define GRU_INPUT  1024
#define GRU_GATES  192

void gru_mv(const ap_uint<8> x[GRU_INPUT],
            float gi[GRU_GATES]);

#endif
