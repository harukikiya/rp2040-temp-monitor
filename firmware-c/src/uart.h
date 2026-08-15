/**
 * @file uart.h
 * @brief UART0 によるログ出力のインタフェース。
 * 
 * @details
 * GPIO0 を TX、GPIO1 を RX に割り当てた UART0 で、115200 bps・8N1・フロー制御なしのログを出す。
 * 受信は現時点では使わない。
 * 
 * @copyright SPDX-License-Identifier: BSD-3-Clause
 */

#ifndef UART_H
#define UART_H

#include <stdint.h>

/** @brief 使用するボーレート[bps]。 */
#define UART_BAUD_RATE      115200u

/**
 * @brief UART0 を初期化する。
 * 
 * @details
 * clocks_init() で clk_peri が確定した後に呼ぶこと。
 * ボーレートの分周比は clk_peri の周波数から計算するため、
 * クロックが未初期化だと正しい速度にならない。
 */
void uart_init(void);

/**
 * @brief 1 文字送信する。
 * @param c 送信する文字。
 * @details 送信 FIFO に空きができるまで待ってから書き込む。
 */
void uart_putc(char c);

/**
 * @brief 文字列を送信する。
 * @param s NUL 終端の文字列。
 * @details 改行（\\n）は CR+LF に変換する。端末での表示崩れを防ぐため。
 */
void uart_puts(const char *s);

/**
 * @brief 符号なし 32 ビット整数を 10 進で送信する。
 * @param value 送信する値。
 */
void uart_put_u32(uint32_t value);

/**
 * @brief 符号なし 32 ビット整数を 16 進 8 桁（0x 付き）で送信する。
 * @param value 送信する値。
 */
void uart_put_hex32(uint32_t value);

#endif  /* UART_H */
