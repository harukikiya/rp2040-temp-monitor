/**
 * @file main.c
 * @brief クロックを初期化し、UART にログを出しながら LED を点滅させる。
 * 
 * @details
 * 段階 2-D-3-2。2-D-3-1 で確立した 125 MHz のクロックを使って UART0 を
 * 115200 bps で動かし、起動時のクロック実測値と動作中のカウンタを出力する。
 * これまで LED と gdb しか無かった観測手段に、文字出力が加わる。
 * 
 * 配線：GPIO0（TX）と GPIO1（RX）を debugprobe の UART 側（U コネクタ）に繋ぐ。
 * 
 * 
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdint.h>

#include "clocks.h"
#include "delay.h"
#include "rp2040_regs.h"
#include "uart.h"

/** @brief オンボード LED が接続された GPIO 番号。 */
#define LED_PIN             25u

/** @brief LED のビットマスク。 */
#define LED_MASK            (1u << LED_PIN)

/** @brief LED の点滅半周期[ミリ秒]。 */
#define BLINK_HALF_MS       500u

/**
 * @brief クロック情報を再表示する間隔（点減半周期の回数）。
 * @details 半周期 500 ms × 20 回 = 10 秒ごと。
 */
#define INFO_INTERVAL_TICKS 20u

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
 * @brief 起動時のクロック実測値を UART に出力する。
 */
static void print_clock_info(void)
{
    uart_puts("\n");
    uart_puts("=== RP2040 temp monitor (stage 2-D-3-2) ===\n");
    uart_puts("XOSC     : ");
    uart_put_u32(g_khz_xosc);
    uart_puts(" kHz\n");
    uart_puts("clk_ref  : ");
    uart_put_u32(g_khz_clk_ref);
    uart_puts(" kHz\n");
    uart_puts("clk_sys  : ");
    uart_put_u32(g_khz_clk_sys);
    uart_puts(" kHz\n");
    uart_puts("clk_peri : ");
    uart_put_u32(g_khz_clk_peri);
    uart_puts(" kHz\n");
    uart_puts("baud     : ");
    uart_put_u32(UART_BAUD_RATE);
    uart_puts("\n");

}

/**
 * @brief アプリケーションのエントリポイント。
 * 
 * @details
 * クロックと UART を初期化し、実測値を出力してから、LED を点滅させながら
 * 経過秒数をログに出す。
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
    uart_init();

    print_clock_info();

    uint32_t half_ticks          = 0u;
    uint32_t ticks_since_info    = 0u;

    for (;;) {
        SIO_GPIO_OUT_XOR = LED_MASK;
        delay_ms(BLINK_HALF_MS);

        /* 半周期ごとに反転するので、2 回で 1 秒 */
        half_ticks++;

        /* 
         * 半周期ごとに 1 増えるので、偶数のとき 1 秒経過。
         * 除算命令が無い Cortex-M0+ でも安全なように、2 の冪の演算に置き換える。
         *      x % 2 → x & 1 ／ x / 2 → x >> 1
         */
        if ((half_ticks & 1u) == 0u) {
            uart_puts("uptime: ");
            uart_put_u32(half_ticks >> 1);
            uart_puts(" s\n");
        }

        /* 
         * 10 秒（半周期 20 回）ごとにクロック情報を出し直す。起動メッセージは
         * 一度しか出ないため、端末を後から接続すると見逃してしまう。
         * 定期的に再表示することで、いつ接続しても状態を確認できるようにする。
         */
        ticks_since_info++;
        if (ticks_since_info >= INFO_INTERVAL_TICKS) {
            ticks_since_info = 0u;
            print_clock_info();
        }
    }
}
