/**
 * @file uart.c
 * @brief UART0 によるログ出力。
 * 
 * @details
 * 段階2-D-3-2。これまでの観測手段は LED と gdb だけだったが、
 * UART0 が通ると実行中の値をそのまま文字で出せるようになる。
 * 
 * ボーレートは clk_peri を分周して作るため、クロック初期化（2-D-3-1）が前提になる。
 * ROSC のままでは周波数が不足なので通信が成立しない。
 * 
 * 標準ライブラリを使わない方針のため、数値の文字列化も自前で行う。
 *
 * @copyright SPDX-License-Identifier: BSD-3-Clause
 */

#include "uart.h"

#include "clocks.h"
#include "rp2040_regs.h"

/** @brief uint32_t の 10 進表現の最大桁数（4294967295 = 10 桁）。 */
#define U32_MAX_DIGITS      10

/** @brief 16 進 1 桁に使う文字。 */
static const char HEX_DIGITS[] = "0123456789ABCDEF";

/**
 * @brief 10 進変換に使う 10 の冪乗（大きい桁から並べる）。
 * 
 * @details
 * Cortex-M0+ には除算命令が無いため、C の `/` や `%` は
 * コンパイラのランタイム関数（__aeabi_uidiv など）の呼び出しになる。
 * 本プロジェクトは -nostdlib でリンクしており、それらは存在しない。
 * そこで「引ける回数を数える」方式で桁を求め、減算と比較だけで 10 進変換する。
 */
static const uint32_t POW10[U32_MAX_DIGITS] = {
    1000000000u, 100000000u, 10000000u, 1000000u, 100000u,
    10000u,      1000u,      100u,      10u,      1u
};

/**
 * @brief 指定したペリフェラルのリセットを解除し、完了を待つ。
 * @param bits RESETS_* のビットマスク。
 */
static void resets_release(uint32_t bits)
{
    RESETS_RESET &= ~bits;
    while ((RESETS_RESET_DONE & bits) != bits) {
        /* 解除完了を待つ */
    }
}

void uart_init(void)
{
    resets_release(RESETS_UART0_BITS);

    /* いったん無効化してから設定する */
    UART0_CR = 0u;

    /* 
     * ボーレート分周比を求める。
     * 
     * PL011 は 16 倍オーバーサンプリングで動作するため、必要な分周比は
     * 
     *  分周比 = clk_peri / ( 16 × ボーレート )
     *        = 125000000 / (16 × 115200 )
     *        = 67.8168...
     * 
     * となり小数になる。PL011 はこれを「整数部 IBRD」と「小数部 FBRD」に分けて指定する。
     * FBRD は 1/64 単位（6 ビット）で表す。
     * 
     * 浮動小数点を使わずに小数部を求めるため、分周比を 128 倍した整数を先に計算する。
     * 16 × 128 = 2048 で、8 / ( 16 × 128 ) = 1/2048 なので、
     * 「8 × クロック ÷ ボーレート」がちょうど分周比の 128 倍になる。
     * 
     *  div = 8 × 125000000 / 115200 = 8680     ← 分周比 67.8168... の 128 倍
     * 
     * ここから整数部と小数部を取り出す。
     * 
     *  div >> 7        … 128 で割ることと同じ（2^7 = 128）
     *                    8680 ÷ 128 = 67.8125 → 整数部 67       …… IBRD
     * 
     *  div & 0x7F      … 下位 7 ビットだけ残す = 128 で割った余り
     *                    8680 - 67 × 128 = 104                 …… 1/128 単位の小数部
     * 
     *  （余り + 1）>> 1 … 1/128 単位を 1/64 単位に直す（2 で割る）。
     *                    +1 は四捨五入のため。
     *                    (104 + 1) ÷ 2 = 52                    …… FBRD
     * 
     * 結果 IBRD = 67、FBRD = 52。実効ボーレードは
     * 125000000 / (16 × (67 + 52/64)) ≒ 115207 bps（誤差 0.006 %）となり、
     * UART が許容する誤差（一般に ±2 % 程度）に十分収まる。
     * 
     * clk_peri と UART_BAUD_RATE はどちらも定数のため、この計算はコンパイル時に畳み込まれ、
     * 実行時の除算は発生しない（Cortex-M0+ には除算命令が無い）。
     */
     const uint32_t div  = (8u * PERI_CLK_HZ) / UART_BAUD_RATE;
     const uint32_t ibrd = div >> 7;                            /* 128 で割った商 */
     const uint32_t fbrd = ((div & 0x7Fu) + 1u) >> 1;           /* 余りを 1/64 単位に */

     UART0_IBRD = ibrd;
     UART0_FBRD = fbrd;

     /* 
      * LCR_H への書き込みで IBRD / FBRD がラッチされる。
      * 順序を逆にするとボーレートが反映されない。
      * 8 ビット・パリティなし・ストップ 1 ビット（8N1）とし、FIFO を有効にする。
      */
      UART0_LCR_H = UART0_LCR_H_WLEN_8BITS | UART0_LCR_H_FEN_BITS;

      /* GPIO0 = TX、GPIO1 = RX に割り当てる */
      IO_BANK0_GPIO_CTRL(UART0_TX_PIN) = IO_BANK0_FUNCSEL_UART;
      IO_BANK0_GPIO_CTRL(UART0_RX_PIN) = IO_BANK0_FUNCSEL_UART;

      /* UART と送受信を有効化する */
      UART0_CR = UART0_CR_UARTEN_BITS | UART0_CR_TXE_BITS | UART0_CR_RXE_BITS;
}

void uart_putc(char c)
{
    /* 送信 FIFO が満杯の間は待つ */
    while ((UART0_FR & UART0_FR_TXFF_BITS) != 0u) {
        /* 空きを待つ */
    }

    UART0_DR = (uint32_t)(unsigned char)c;
}

void uart_puts(const char *s)
{
    while (*s != '\0') {
        if (*s == '\n') {
            uart_putc('\r');
        }
        uart_putc(*s);
        s++;
    }
}

void uart_put_u32(uint32_t value)
{
    /* 先頭の 0 を出力し始めたかどうか（0 埋めを避けるため） */
    uint32_t started = 0u;

    for (uint32_t i = 0u; i < U32_MAX_DIGITS; i++) {
        uint32_t digit = 0u;

        /* この桁の重みで何回引けるかがその桁の値になる */
        while (value >= POW10[i]) {
            value -= POW10[i];
            digit++;
        }

        /* 最上位から続く 0 は出さない。ただし最下位桁は値が 0 でも必ず出す */
        if ((digit != 0u) || (started != 0u) || (i == (U32_MAX_DIGITS - 1u))) {
            uart_putc((char)('0' + digit));
            started = 1u;
        }
    }
}

void uart_put_hex32(uint32_t value)
{
    uart_puts("0x");

    /* 上位ニブルから 8 桁ぶん出す */
    for (int32_t shift = 28; shift >= 0; shift -= 4) {
        uart_putc(HEX_DIGITS[(value >> shift) & 0xFu]);
    }
}
