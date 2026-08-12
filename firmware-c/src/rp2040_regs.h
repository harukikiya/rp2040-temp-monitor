/**
 * @file rp2040_regs.h
 * @brief C コードが使用する RP2040 レジスタ定義（自前実装）
 *
 * @details
 * 本プロジェクトは pico-sdk を使わないため、C から触るレジスタも自前で定義する。
 * boot2 用の rp2040_boot_regs.h（アセンブリ用）と対になる、C 用の最小定義。
 * 必要になったレジスタを段階的に追加していく。
 *
 * SVD から生成した include/generated/RP2040.h は CMSIS デバイスヘッダであり、
 * ARM の CMSIS-Core（core_cm0plus.h）と system_RP2040.h を必要とする。これらは
 * 本リポジトリに含めていないため、現時点では本ファイルを使う。
 *
 * 各値の出典：RP2040 データシート Section 2.14（RESETS）、2.19（GPIO / IO_BANK0）、
 * 2.3.1（SIO）。
 *
 * @copyright SPDX-License-Identifier: BSD-3-Clause
 */

#ifndef RP2040_REGS_H
#define RP2040_REGS_H

#include <stdint.h>

/**
 * @brief 絶対アドレスを 32 ビットレジスタとして参照するためのマクロ。
 * @param addr レジスタの絶対アドレス。
 * @details volatile を付けることで、コンパイラによる読み書きの最適化を防ぐ。
 */
#define REG32(addr)                 (*(volatile uint32_t *)(addr))

/* ============================================================
 * ベースアドレス
 * ============================================================ */

/** サブシステムリセット制御のベースアドレス */
#define RESETS_BASE                 0x4000C000u

/** バンク0 GPIO の機能選択・制御のベースアドレス */
#define IO_BANK0_BASE               0x40014000u

/** SIO（Single-cycle IO）のベースアドレス。コアから 1 サイクルでアクセスできる */
#define SIO_BASE                    0xD0000000u

/* ============================================================
 * RESETS（データシート 2.14）
 * ビットが 1 = リセット中、0 = リセット解除。
 * ============================================================ */

/** リセット制御レジスタ */
#define RESETS_RESET                REG32(RESETS_BASE + 0x00u)

/** リセット解除完了レジスタ（該当ビットが 1 で使用可能） */
#define RESETS_RESET_DONE           REG32(RESETS_BASE + 0x08u)

/** RESET / RESET_DONE の IO_BANK0 ビット（bit 5） */
#define RESETS_IO_BANK0_BITS        (1u << 5)

/** RESET / RESET_DONE の PADS_BANK0 ビット（bit 8） */
#define RESETS_PADS_BANK0_BITS      (1u << 8)

/* ============================================================
 * IO_BANK0（データシート 2.19）
 * GPIO ごとに STATUS(4B) + CTRL(4B) の 8 バイトが並ぶ。
 * ============================================================ */

/**
 * @brief 指定 GPIO の CTRL レジスタ。
 * @param n GPIO 番号（0〜29）。
 */
#define IO_BANK0_GPIO_CTRL(n)       REG32(IO_BANK0_BASE + 0x04u + ((n) * 8u))

/** CTRL の FUNCSEL フィールド（bit 4:0）に入れる SIO の値 */
#define IO_BANK0_FUNCSEL_SIO        5u

/* ============================================================
 * SIO（データシート 2.3.1）
 * SET / CLR / XOR 専用レジスタを持ち、read-modify-write なしで
 * 単一ビットを操作できる。
 * ============================================================ */

/** GPIO 出力値（直接書き込み） */
#define SIO_GPIO_OUT                REG32(SIO_BASE + 0x10u)

/** GPIO 出力値セット（書いたビットを 1 にする） */
#define SIO_GPIO_OUT_SET            REG32(SIO_BASE + 0x14u)

/** GPIO 出力値クリア（書いたビットを 0 にする） */
#define SIO_GPIO_OUT_CLR            REG32(SIO_BASE + 0x18u)

/** GPIO 出力値反転（書いたビットを反転する） */
#define SIO_GPIO_OUT_XOR            REG32(SIO_BASE + 0x1Cu)

/** GPIO 出力イネーブルセット（書いたビットを出力にする） */
#define SIO_GPIO_OE_SET             REG32(SIO_BASE + 0x24u)

/** GPIO 出力イネーブルクリア（書いたビットを入力にする） */
#define SIO_GPIO_OE_CLR             REG32(SIO_BASE + 0x28u)

#endif /* RP2040_REGS_H */