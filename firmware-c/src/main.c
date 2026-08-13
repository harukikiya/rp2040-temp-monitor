/**
 * @file main.c
 * @brief クロックを初期化し、正確な周期で LED を点滅させる。
 * 
 * @details
 * 段階 2-D-3-1。ROSC（約 6.5 MHz、精度なし）から XOSC + PLL による 125 MHz へ
 * 切り替え、TIMER を使って正確に 500 ms 周期で LED を点滅させる。
 * 
 * クロックが正しく設定できたかは周波数カウンタ（FC0）で実測し、結果をグローバル変数に保存する。
 * UART がまだ無いため、値は gdb で読み出して確認する。
 * 
 * @note 期待値：clk_sys = 125000 kHz、clk_peri = 125000 kHz、XOSC = 12000 kHz。
 * 
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdint.h>

#include "clocks.h"
#include "delay.h"
#include "rp2040_regs.h"

/** @brief オンボード LED が接続された GPIO 番号。 */
#define LED_PIN             25u

/** @brief LED のビットマスク。 */
#define LED_MASK            (1u << LED_PIN)

/** @brief LED の点滅半周期[ミリ秒]。 */
#define BLINK_HALF_MS       500u

/**
 * @name 周波数の実測値（gdb で確認するためのグローバル変数）
 * @brief clocks_init() 後に FC0 で測定した値[kHz]。
 * @details .bss ではなく .data に置いて初期値を持たせることで、crt0 の
 *          .data コピーが働いていることも同時に確認できる。
 * @{
 */
volatile uint32_t g_khz_xosc     = 1u;
volatile uint32_t g_khz_clk_ref  = 1u;
volatile uint32_t g_khz_clk_sys  = 1u;
volatile uint32_t g_khz_clk_peri = 1u;
/** @} */

/**
 * @brief IO_BANK0 と PAD_BANK0 のリセットを解除する。
 * 
 * @details
 * RP2040 はリセット直後、ほとんどのペリフェラルがリセット状態にある。
 * RESET レジスタの該当ビットを 0 にして解除し、RESET_DONE で完了を待つ。
 * 待たずにレジスタへ書くと設定が失われる。
 */
static void gpio_reset_release(void)
{
    const uint32_t mask = RESETS_IO_BANK0_BITS | RESETS_PADS_BANK0_BITS;

    RESETS_RESET &= ~mask;
    while ((RESETS_RESET_DONE & mask) != mask) {
        /* 解除完了を待つ */
    }
}

/**
 * @brief LED 用に GPIO25 を出力として初期化する。
 */
static void led_init(void)
{
    IO_BANK0_GPIO_CTRL(LED_PIN) = IO_BANK0_FUNCSEL_SIO;

    SIO_GPIO_OE_SET     = LED_MASK;
    SIO_GPIO_OUT_CLR    = LED_MASK;
}

/**
 * @brief 概算の遅延を行う。
 * 
 * @details
 * タイマをまだ使わないため、単純な減算ループで時間を潰す。
 * 引数を volatile にすることで、最適化が有効な場合でもループが削除されないようにする。
 * 
 * @param count ループ回数。
 */
static void delay_loop(volatile uint32_t count)
{
    while (count > 0u) {
        count--;
    }
}

/**
 * @brief アプリケーションのエントリポイント。
 * 
 * @details
* クロックを初期化し、各クロックの実測値を保存してから LED を点滅させる。
 * 組み込みのため戻らない。
 * 
 * @return int 形式上の戻り値（実際には戻らない）。
 */
int main(void)
{

    clocks_init();

    g_khz_xosc      = clocks_measure_khz(FC0_SRC_XOSC);
    g_khz_clk_ref   = clocks_measure_khz(FC0_SRC_CLK_REF);
    g_khz_clk_sys   = clocks_measure_khz(FC0_SRC_CLK_SYS);
    g_khz_clk_peri  = clocks_measure_khz(FC0_SRC_CLK_PERI);

    gpio_reset_release();
    led_init();

    for (;;) {
        SIO_GPIO_OUT_XOR = LED_MASK;
        delay_ms(BLINK_HALF_MS);
    }
}
