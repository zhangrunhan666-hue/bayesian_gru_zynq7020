/*
 * PS + PL GRU inference with MC Dropout.
 *
 * PL  : gru_mv IP computes gi_raw = W_ih * x + b_ih
 * PS  : dropout + W_hh + gates + FC + entropy / reject
 */

#include "weights.h"
#include "ff.h"
#include "xgru_mv.h"
#include "xparameters.h"
#include "xil_printf.h"
#include "xiltimer.h"

#include <math.h>
#include <string.h>

#define GRU_GATES (3 * GRU_HIDDEN)
#define MC_K_MIN 3
#define MC_K_MAX 5
#define EARLY_ENT 0.30f
#define DROP_P 0.15f
#define DROP_INV (1.0f / (1.0f - DROP_P))
#define REJECT_ENT 0.50f

#define CLIP_COUNT 1611
#define CLIP_T 8
#define CLIP_S 32

static XGru_mv gru;

static FATFS fs;
static FIL fil;
static unsigned char labels[CLIP_COUNT];
static unsigned char clipbuf[CLIP_T][CLIP_S * CLIP_S];

static float h_state[GRU_HIDDEN];
static float gi[GRU_GATES];
static float gh[GRU_GATES];
static float logits[GRU_CLASSES];
static unsigned char xdrop[GRU_INPUT];
static float hdrop[GRU_HIDDEN];

static unsigned int rng_state = 0x12345678u;

static unsigned int xorshift32(void)
{
    unsigned int x = rng_state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    rng_state = x;
    return x;
}

static int keep_unit(void)
{
    return ((xorshift32() & 0xFFFFu) <
            (unsigned int)((1.0f - DROP_P) * 65536.0f));
}

static float sigmoidf(float x)
{
    if (x < -30.0f) return 0.0f;
    if (x >  30.0f) return 1.0f;
    return 1.0f / (1.0f + expf(-x));
}

static int argmax3(const float *v)
{
    int best = 0;
    if (v[1] > v[best]) best = 1;
    if (v[2] > v[best]) best = 2;
    return best;
}

static void gh_matvec(const float *hv)
{
    int o, i;
    for (o = 0; o < GRU_GATES; ++o) {
        float acc = 0.0f;
        for (i = 0; i < GRU_HIDDEN; ++i) {
            acc += (float)W_hh[o * GRU_HIDDEN + i] * hv[i];
        }
        gh[o] = acc * W_hh_scale + (float)b_hh[o] * b_hh_scale;
    }
}

static int gru_forward_mc(const unsigned char *frames, float *out_logits)
{
    int t, i, c;

    for (i = 0; i < GRU_HIDDEN; ++i) {
        h_state[i] = 0.0f;
    }

    for (t = 0; t < GRU_T; ++t) {
        const unsigned char *frame = frames + (long)t * GRU_INPUT;
        u32 done = 0;
        u32 timeout = 0;

        /* Input dropout, then PL: gi_raw = W_ih * x_drop + b_ih */
        for (i = 0; i < GRU_INPUT; ++i) {
            xdrop[i] = keep_unit() ? frame[i] : 0;
        }

        XGru_mv_Write_x_Bytes(&gru, 0, (char *)xdrop, GRU_INPUT);
        XGru_mv_Start(&gru);
        while (!done && timeout < 50000000u) {
            done = XGru_mv_IsDone(&gru);
            timeout++;
        }
        if (!done) {
            xil_printf("IP TIMEOUT\r\n");
            return -1;
        }

        {
            u32 giw[GRU_GATES];
            int k;
            XGru_mv_Read_gi_Words(&gru, 0, giw, GRU_GATES);
            for (k = 0; k < GRU_GATES; ++k) {
                union { u32 u; float f; } cv;
                cv.u = giw[k];
                gi[k] = cv.f;
            }
            /* Undo HLS missing /255, then inverted dropout scaling. */
            for (k = 0; k < GRU_GATES; ++k) {
                float bi = (float)b_ih[k] * b_ih_scale;
                gi[k] = (gi[k] - bi) * (1.0f / 255.0f) + bi;
                gi[k] = (gi[k] - bi) * DROP_INV + bi;
            }
        }

        /* Hidden dropout, then gh = W_hh * h_drop + b_hh */
        for (i = 0; i < GRU_HIDDEN; ++i) {
            hdrop[i] = keep_unit() ? h_state[i] * DROP_INV : 0.0f;
        }
        gh_matvec(hdrop);

        for (i = 0; i < GRU_HIDDEN; ++i) {
            float r = sigmoidf(gi[i] + gh[i]);
            float z = sigmoidf(gi[GRU_HIDDEN + i] + gh[GRU_HIDDEN + i]);
            float n = tanhf(gi[2 * GRU_HIDDEN + i] + r * gh[2 * GRU_HIDDEN + i]);
            h_state[i] = (1.0f - z) * n + z * hdrop[i];
        }
    }

    /* FC dropout */
    for (i = 0; i < GRU_HIDDEN; ++i) {
        hdrop[i] = keep_unit() ? h_state[i] * DROP_INV : 0.0f;
    }
    for (c = 0; c < GRU_CLASSES; ++c) {
        float acc = 0.0f;
        for (i = 0; i < GRU_HIDDEN; ++i) {
            acc += (float)W_fc[c * GRU_HIDDEN + i] * hdrop[i];
        }
        out_logits[c] = acc * W_fc_scale + (float)b_fc[c] * b_fc_scale;
    }
    return 0;
}

int main(void)
{
    XTime t_start, t_end;
    int n, c, k, pred, correct = 0;
    int class_total[GRU_CLASSES];
    int class_correct[GRU_CLASSES];
    u32 total_ms, avg_ms;
    int rejected = 0;
    int accepted = 0;
    int accept_correct = 0;
    int reject_correct = 0;
    float ent_sum = 0.0f, max_ent = -1.0f;
    float ent_correct_sum = 0.0f, ent_wrong_sum = 0.0f;
    int max_idx = 0;
    int k3 = 0, k4 = 0, k5 = 0;
    uint32_t hdr[4];
    UINT br;
    FRESULT fr;

    for (c = 0; c < GRU_CLASSES; ++c) {
        class_total[c] = 0;
        class_correct[c] = 0;
    }

    if (XGru_mv_Initialize(&gru, XPAR_XGRU_MV_0_BASEADDR) != XST_SUCCESS) {
        xil_printf("ERROR: gru_mv init failed\r\n");
        while (1) { }
    }

    fr = f_mount(&fs, "0:", 1);
    if (fr != FR_OK) {
        xil_printf("ERROR: f_mount %d\r\n", (int)fr);
        while (1) { }
    }
    fr = f_open(&fil, "0:/CLIPS.BIN", FA_READ);
    if (fr != FR_OK) {
        xil_printf("ERROR: f_open %d\r\n", (int)fr);
        while (1) { }
    }
    fr = f_read(&fil, hdr, 16, &br);
    if (fr != FR_OK || br != 16 || memcmp(hdr, "JCLP", 4) != 0 ||
        hdr[1] != CLIP_COUNT || hdr[2] != CLIP_T || hdr[3] != CLIP_S) {
        xil_printf("ERROR: CLIPS.BIN header\r\n");
        while (1) { }
    }
    fr = f_read(&fil, labels, CLIP_COUNT, &br);
    if (fr != FR_OK || br != CLIP_COUNT) {
        xil_printf("ERROR: labels\r\n");
        while (1) { }
    }

    xil_printf("\r\nJester GRU PS+PL: 8 x 32 x 32, H=%d, classes=%d\r\n",
               GRU_HIDDEN, GRU_CLASSES);
    xil_printf("clips=%d  IP base=0x%08x\r\n",
               CLIP_COUNT, (unsigned)XPAR_XGRU_MV_0_BASEADDR);
    xil_printf("Adaptive MC: Kmin=%d Kmax=%d earlyH<%.2f p=%.2f\r\n",
               MC_K_MIN, MC_K_MAX, (double)EARLY_ENT, (double)DROP_P);
    xil_printf("CLIPS.BIN loaded from SD\r\n");
    xil_printf("inferencing %d clips...\r\n", CLIP_COUNT);

    XTime_GetTime(&t_start);

    for (n = 0; n < CLIP_COUNT; ++n) {
        int label = (int)labels[n];
        float prob_sum[GRU_CLASSES] = {0.0f, 0.0f, 0.0f};
        float ent = 0.0f;

        fr = f_read(&fil, clipbuf, sizeof(clipbuf), &br);
        if (fr != FR_OK || br != sizeof(clipbuf)) {
            xil_printf("ERROR: read clip %d\r\n", n);
            while (1) { }
        }

        {
            int k_used = 0;
            for (k = 0; k < MC_K_MAX; ++k) {
                float maxv, sum;
                float tmp[GRU_CLASSES];
                float ent_tmp = 0.0f;

                if (gru_forward_mc(&clipbuf[0][0], logits) != 0) {
                    xil_printf("ERROR at clip %d\r\n", n);
                    while (1) { }
                }
                maxv = logits[0];
                for (c = 1; c < GRU_CLASSES; ++c) {
                    if (logits[c] > maxv) maxv = logits[c];
                }
                sum = 0.0f;
                for (c = 0; c < GRU_CLASSES; ++c) {
                    logits[c] = expf(logits[c] - maxv);
                    sum += logits[c];
                }
                for (c = 0; c < GRU_CLASSES; ++c) {
                    prob_sum[c] += logits[c] / sum;
                }
                k_used++;

                if (k_used >= MC_K_MIN) {
                    for (c = 0; c < GRU_CLASSES; ++c) {
                        tmp[c] = prob_sum[c] / (float)k_used;
                        ent_tmp -= tmp[c] * logf(tmp[c] + 1e-8f);
                    }
                    if (ent_tmp < EARLY_ENT) {
                        break;
                    }
                }
            }
            if (k_used == 3) k3++;
            else if (k_used == 4) k4++;
            else k5++;

            for (c = 0; c < GRU_CLASSES; ++c) {
                prob_sum[c] /= (float)k_used;
                ent -= prob_sum[c] * logf(prob_sum[c] + 1e-8f);
            }
        }
        pred = argmax3(prob_sum);

        class_total[label]++;
        if (pred == label) {
            correct++;
            class_correct[label]++;
            ent_correct_sum += ent;
        } else {
            ent_wrong_sum += ent;
        }
        if (ent > REJECT_ENT) {
            rejected++;
            if (pred == label) reject_correct++;
        } else {
            accepted++;
            if (pred == label) accept_correct++;
        }
        ent_sum += ent;
        if (ent > max_ent) {
            max_ent = ent;
            max_idx = n;
        }

        xil_printf(".");
        if (((n + 1) % 100) == 0) {
            xil_printf(" %d/%d\r\n", n + 1, CLIP_COUNT);
        }
    }

    f_close(&fil);
    XTime_GetTime(&t_end);
    total_ms = (u32)((t_end - t_start) / (COUNTS_PER_SECOND / 1000));
    avg_ms = total_ms / CLIP_COUNT;

    xil_printf("done: %d/%d correct\r\n", correct, CLIP_COUNT);
    for (c = 0; c < GRU_CLASSES; ++c) {
        xil_printf("%s: %d/%d\r\n", GRU_CLASS_NAMES[c], class_correct[c], class_total[c]);
    }
    xil_printf("mean entropy: %d/1000\r\n", (int)(ent_sum / CLIP_COUNT * 1000.0f));
    xil_printf("accept H<=0.50: %d/%d, acc=%d/1000\r\n",
               accept_correct, accepted,
               accepted ? (int)(1000.0f * accept_correct / accepted) : 0);
    xil_printf("reject H>0.50: %d/%d, acc=%d/1000\r\n",
               reject_correct, rejected,
               rejected ? (int)(1000.0f * reject_correct / rejected) : 0);
    xil_printf("mean entropy correct: %d/1000, wrong: %d/1000\r\n",
               correct ? (int)(ent_correct_sum / correct * 1000.0f) : 0,
               (CLIP_COUNT - correct) ? (int)(ent_wrong_sum / (CLIP_COUNT - correct) * 1000.0f) : 0);
    xil_printf("max entropy: clip %d, H=%d/1000\r\n",
               max_idx, (int)(max_ent * 1000.0f));
    xil_printf("time: %d ms total, %d ms/clip\r\n", total_ms, avg_ms);
    xil_printf("adaptive K counts: K3=%d K4=%d K5=%d\r\n", k3, k4, k5);
    xil_printf("PC det accuracy: 1285/1611\r\n");

    while (1) {
        /* keep UART alive */
    }
    return 0;
}
