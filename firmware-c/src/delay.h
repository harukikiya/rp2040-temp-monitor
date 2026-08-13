/**
 * @file delay.h
 * @brief TIMER を使った時間待ち。
 * 
 * @details
 * clocks_init() で WATCHDOG の TICK を設定した後に使うこと。TIMER は
 * 1 マイクロ秒刻みの自走カウンタで、クロックを初期化していれば水晶の精度で時間を測れる。
 * 遅延ループと違ってコンパイラの最適化やクロック変更の影響を受けない。
 * 
 * @copyright SPDX-License-Identifier: BSD-3-Clause
 */
#ifndef DELAY_H
#define DELAY_H

#include <stdint.h>

#include "rp2040_regs.h"

/**
 * @brief 指定したマイクロ秒だけ待つ。
 * 
 * @details
 * 32 ビットの自走カウンタの差分で判定するため、約 71 分でのラップアラウンドを
 * またいでも正しく動作する（符号なし演算の性質による）。
 * 
 * @param us 待ち時間[マイクロ秒]。
 */
static inline void delay_us(uint32_t us)
{
    const uint32_t start = TIMER_TIMERAWL;

    while ((TIMER_TIMERAWL - start) < us) {
        /* 経過を待つ */
    }
}

/**
 * @brief 指定したミリ秒だけ待つ。
 * @param ms 待ち時間[ミリ秒]。
 */
static inline void delay_ms(uint32_t ms)
{
    while (ms > 0u) {
        delay_us(1000u);
        ms--;
    }
}

#endif  /* DELAY_H */
