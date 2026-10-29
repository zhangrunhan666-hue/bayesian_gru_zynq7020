#include "gru_mv.h"
#include "tb_data.h"

#include <cmath>
#include <cstdio>

int main()
{
    ap_uint<8> x[GRU_INPUT];
    float gi[GRU_GATES];

    for (int i = 0; i < GRU_INPUT; ++i) {
        x[i] = TB_X[i];
    }

    gru_mv(x, gi);

    int errors = 0;
    float max_gi = 0.0f;
    for (int i = 0; i < GRU_GATES; ++i) {
        float e1 = std::fabs(gi[i] - TB_GI[i]);
        if (e1 > max_gi) max_gi = e1;
        if (e1 > 1e-3f) {
            if (errors < 8) {
                std::printf("MISMATCH %d gi=%f exp=%f\n", i, gi[i], TB_GI[i]);
            }
            errors++;
        }
    }

    std::printf("max_gi_err=%f errors=%d\n", max_gi, errors);
    return errors ? 1 : 0;
}
