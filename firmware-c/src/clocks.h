/**
 * @file clocks.h
 * @brief クロック初期化と周波数測定のインタフェース。
 * 
 * @copyright SPDX-License-Identifier: BSD-3-Clause
 */

#ifndef CLOCKS_H
#define CLOCKS_H

#include <stdint.h>

/** @brief 初期化後のシステムクロック周波数[Hz]。 */
#define SYS_CLK_HZ      125000000u

/** @brief 初期化後のペリフェラルクロック周波数[Hz]（clk_sys と同じ）。 */
#define PERI_CLK_HZ     SYS_CLK_HZ

/**
 * @brief XOSC と PLL と初期化し、clk_sys を 125 MHz にする。
 * 
 * @details
 * リセット直後は ROSC（約 6.5 MHz、精度なし）で動作している。
 * 本関数は 12 MHz の水晶（XOSC）を起動し、PLL_SYS で 125 MHz を生成して
 * clk_sys / clk_peri に供給する。あわせて TIMER が 1 マイクロ秒刻みで
 * 動くように WATCHDOG の TICK 生成器を設定する。
 * 
 * @note フラッシュの XIP は boot2 が設定した分周のまま動作する。
 */
void clocks_init(void);

/**
 * @brief 周波数カウンタ（FC0）で指定クロックの周波数を測定する。
 * 
 * @details clk_ref を基準に実測する。clocks_init() の後に呼ぶこと。
 * 
 * @param src 測定対象（rp2040_regs.h の FC0_SRC_* を渡す）。
 * @return uint32_t 測定された周波数[kHz]。
 */
uint32_t clocks_measure_khz(uint32_t src);

#endif  /* CLOCKS_H */
