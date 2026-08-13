/**
 * @file clocks.c
 * @brief クロック初期化（XOSC → PLL_SYS → clk_sys / clk_peri）。
 * 
 * @details
 * 段階 2-D-3-1。リセット直後は ROSC（リングオシレータ、約 6.5 MHz）で動いており、
 * 周波数が個体差・温度で変動するため時間もボーレートも決められない。本ファイルで
 * 12 MHz の水晶を基準にした 125 MHz を作り、以降の正確な時間制御を可能にする。
 * 
 * 手順（データシート 2.15 の推奨順）：
 *      1. resus（クロック停止時の自動復旧）を無効化する
 *      2. XOSC を起動して安定を待つ
 *      3. clk_sys と clk_ref を PLL から切り離す（PLL を再設定するため）
 *      4. PLL_SYS を 125 MHz に設定する
 *      5. clk_ref を XOSC に切り替える
 *      6. clk_sys を PLL_SYS に切り替える
 *      7. clk_peri を clk_sys に接続して有効化する
 *      8. TIMER 用の 1 MHz TICK を設定する
 * 
 * @copyright SPDX-License-Identifier: BSD-3-Clause
 */

#include "clocks.h"
#include "rp2040_regs.h"

/** @brief PLL の基準分周比（12 MHz をそのまま使う）。 */
#define PLL_REFDIV      1u

/** @brief VCO の逓倍数。12 MHz × 125 = 1500 MHz。 */
#define PLL_FBDIV       125u

/** @brief ポストディバイダ1。1500 MHz ÷ 6 ÷ 2 = 125 MHz */
#define PLL_POSTDIV1    6u

/** @brief ポストディバイダ2。 */
#define PLL_POSTDIV2    2u

/**
 * @brief 指定したペリフェラルのリセットを解除し、完了を待つ。
 * 
 * @param bits RESETS_* のビットマスク。
 */
static void resets_release(uint32_t bits)
{
    RESETS_RESET &= ~bits;
    while ((RESETS_RESET_DONE & bits) != bits) {
        /* 解除完了を待つ */
    }
}

/**
 * @brief XOSC（12 MHz 水晶）を起動し、発振が安定するまで待つ。
 * 
 * @details
 * 起動待ち時間を STARTUP に設定してから ENABLE を書く。ENABLE には誤書き込み防止の
 * マジック値（0xFAB）が必要で、単純な 1 では有効化されない。
 */
static void xosc_init(void)
{
    XOSC_CTRL       = XOSC_CTRL_FREQ_RANGE_1_15MHZ;
    XOSC_STARTUP    = XOSC_STARTUP_DELAY;
    XOSC_CTRL       = XOSC_CTRL_FREQ_RANGE_1_15MHZ | XOSC_CTRL_ENABLE_VALUE;

    while ((XOSC_STATUS & XOSC_STATUS_STABLE_BITS) == 0u) {
        /* 発振が安定するまで待つ */
    }
}

/**
 * @brief PLL_SYS を 125 MHz に設定する。
 * 
 * @details
 * VCO を先に立ち上げてロックを待ち、その後ポストディバイダを設定して電源を入れる。
 * 順序を守らないとロックしないか、意図しない周波数が出る。
 */
static void pll_sys_init(void)
{
    resets_release(RESETS_PLL_SYS_BITS);

    /* いったん全電源を落としてから設定する */
    PLL_SYS_PWR         = 0xFFFFFFFFu;
    PLL_SYS_FBDIV_INT   = 0u;

    PLL_SYS_CS          = PLL_REFDIV;
    PLL_SYS_FBDIV_INT   = PLL_FBDIV;

    /* VCO を起動してロックを待つ */
    PLL_SYS_PWR &= ~(PLL_PWR_PD_BITS | PLL_PWR_VCOPD_BITS);
    while ((PLL_SYS_CS & PLL_CS_LOCK_BITS) == 0u) {
        /* ロックを待つ */
    }

    /* ポストディバイダを設定してから電源を入れる */
    PLL_SYS_PRIM = (PLL_POSTDIV1 << PLL_PRIM_POSTDIV1_LSB)
                 | (PLL_POSTDIV2 << PLL_PRIM_POSTDIV2_LSB);
    PLL_SYS_PWR &= ~PLL_PWR_POSTDIVPD_BITS;
}

void clocks_init(void)
{
    /* 1. resus を無効化する（クロック源を切り替える間に誤動作させない） */
    CLK_SYS_RESUS_CTRL = 0u;

    /* 2. XOSC 起動 */
    xosc_init();

    /* 3. clk_sys と clk_ref を PLL から切り離す。
     *    クロックの切替スイッチ（マルチプレクサ）は2段構成になっている。
     *    SRC 側は切替中も異常なパルス（グリッチ）が出ない設計だが、AUX 側は
     *    そうではない。CPU が AUX 経由のクロックで動いたまま AUX を切り替えると
     *    暴走する。そこで PLL を再設定する前に、SRC を安全な側（clk_ref / ROSC）
     *    へ逃がしておく。 */
    CLK_SYS_CTRL &= ~CLK_REF_CTRL_SRC_MASK;
    while (CLK_SYS_SELECTED != CLK_SYS_SELECTED_REF) {
        /* 切り替え完了を待つ */
    }
    CLK_REF_CTRL &= ~CLK_REF_CTRL_SRC_MASK;
    while (CLK_REF_SELECTED != CLK_REF_SELECTED_ROSC) {
        /* 切り替え完了を待つ */
    }

    /* 4. PLL_SYS = 125 MHz */
    pll_sys_init();

    /* 5. clk_ref = XOSC（12 MHz）。TIMER の TICK もこれを基準にする */
    CLK_REF_DIV     = CLK_DIV_1;
    CLK_REF_CTRL    = (CLK_REF_CTRL & ~CLK_REF_CTRL_SRC_MASK) | CLK_REF_SRC_XOSC;
    while (CLK_REF_SELECTED != CLK_REF_SELECTED_XOSC) {
        /* 切り替え完了を待つ */
    }

    /* 6. clk_sys = PLL_SYS（125 MHz）。
     *    周波数を上げる場合は分周を先に設定してから切り替える。 */
    CLK_SYS_DIV  = CLK_DIV_1;
    CLK_SYS_CTRL = (CLK_SYS_CTRL & ~CLK_CTRL_AUXSRC_MASK)
                 | (CLK_SYS_AUXSRC_PLL_SYS << CLK_CTRL_AUXSRC_LSB);
    CLK_SYS_CTRL |= CLK_SYS_SRC_AUX;
    while (CLK_SYS_SELECTED != CLK_SYS_SELECTED_AUX) {
        /* 切り替え完了を待つ */
    }

    /* 7. clk_peri = clk_sys（UART などのペリフェラル用） */
    CLK_PERI_CTRL = 0u;
    CLK_PERI_CTRL = (CLK_PERI_AUXSRC_CLK_SYS << CLK_CTRL_AUXSRC_LSB)
                  | CLK_PERI_CTRL_ENABLE_BITS;

    /* 8. TIMERが 1 マイクロ秒刻みで進むように TICK を設定する。
     *    clk_ref（12 MHz）を 12 分周して 1 MHz を作る。 */
    resets_release(RESETS_TIMER_BITS);
    WATCHDOG_TICK = XOSC_MHZ | WATCHDOG_TICK_ENABLE_BITS;
}

uint32_t clocks_measure_khz(uint32_t src)
{
    /* 基準は clk_ref（XOSC 12 MHz = 12000 kHz） */
    FC0_REF_KHZ  = XOSC_MHZ * 1000u;
    FC0_MIN_KHZ  = 0u;
    FC0_MAX_KHZ  = 0x1FFFFFFFu;
    FC0_DELAY    = 1u;
    FC0_INTERVAL = 10u;

    FC0_SRC = src;
    while ((FC0_STATUS & FC0_STATUS_DONE_BITS) == 0u) {
        /* 測定完了を待つ */
    }

    const uint32_t result = FC0_RESULT >> FC0_RESULT_KHZ_LSB;

    FC0_SRC = FC0_SRC_NONE;

    return result;
}
