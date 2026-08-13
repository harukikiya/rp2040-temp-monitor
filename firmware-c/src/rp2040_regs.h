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
 * 2.3.1（SIO）、2.15（CLOCKS）、2.16（XOSC）、2.18（PLL）、4.6（TIMER）、4.7（WATCHDOG）。
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

/** RESET / RESET_DONE の PLL_SYS ビット（bit 12） */
#define RESETS_PLL_SYS_BITS         (1u << 12)

/** RESET / RESET_DONE の TIMER ビット（bit 21） */
#define RESETS_TIMER_BITS           (1u << 21)

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


/* ============================================================
 * XOSC（データシート 2.16）
 * 12 MHz の水晶発振子。ROSC より正確で、PLL の基準となる。
 * ============================================================ */

/** 水晶発振器のベースアドレス */
#define XOSC_BASE                   0x40024000u

/** XOSC 制御レジスタ（FREQ_RANGE: bit 11:0、ENABLE: bit 23:12） */
#define XOSC_CTRL                   REG32(XOSC_BASE + 0x00u)

/** XOSC 状態レジスタ（STABLE: bit 31） */
#define XOSC_STATUS                 REG32(XOSC_BASE + 0x04u)

/** XOSC 起動遅延レジスタ（DELAY: bit 13:0） */
#define XOSC_STARTUP                REG32(XOSC_BASE + 0x0Cu)

/** FREQ_RANGE に書く値（1〜15 MHz レンジ） */
#define XOSC_CTRL_FREQ_RANGE_1_15MHZ 0xAA0u

/** ENABLE に書く値（誤書き込み防止のマジック値。bit 23:12 に配置する） */
#define XOSC_CTRL_ENABLE_VALUE      (0xFABu << 12)

/** STATUS の STABLE ビット（発振が安定したら 1） */
#define XOSC_STATUS_STABLE_BITS     (1u << 31)

/** 基板に実装された水晶の周波数[MHz] */
#define XOSC_MHZ                    12u

/**
 * @brief XOSC の起動待ち時間（STARTUP.DELAY に書く値）。
 * @details 1 ms 相当。DELAY 1 カウントが 256 サイクルに対応するため、
 *          (12 MHz / 1000) / 256 を四捨五入して求める。
 */
#define XOSC_STARTUP_DELAY          (((XOSC_MHZ * 1000u) + 128u) / 256u)

/* ============================================================
 * PLL_SYS（データシート 2.18）
 * XOSC を逓倍してシステムクロックを作る。
 * ============================================================ */

/** システム PLL のベースアドレス */
#define PLL_SYS_BASE                0x40028000u

/** PLL 制御・状態（REFDIV: bit 5:0、LOCK: bit 31） */
#define PLL_SYS_CS                  REG32(PLL_SYS_BASE + 0x00u)

/** PLL 電源制御（PD: bit 0、DSMPD: bit 2、POSTDIVPD: bit 3、VCOPD: bit 5） */
#define PLL_SYS_PWR                 REG32(PLL_SYS_BASE + 0x04u)

/** VCO 逓倍数（FBDIV_INT: bit 11:0） */
#define PLL_SYS_FBDIV_INT           REG32(PLL_SYS_BASE + 0x08u)

/** ポストディバイダ（POSTDIV1: bit 18:16、POSTDIV2: bit 14:12） */
#define PLL_SYS_PRIM                REG32(PLL_SYS_BASE + 0x0Cu)

/** CS の LOCK ビット（PLL がロックしたら 1） */
#define PLL_CS_LOCK_BITS            (1u << 31)

/** PWR の PD（主電源断）ビット */
#define PLL_PWR_PD_BITS             (1u << 0)

/** PWR の POSTDIVPD（ポストディバイダ電源断）ビット */
#define PLL_PWR_POSTDIVPD_BITS      (1u << 3)

/** PWR の VCOPD（VCO 電源断）ビット */
#define PLL_PWR_VCOPD_BITS          (1u << 5)

/** PRIM の POSTDIV1 のビット位置 */
#define PLL_PRIM_POSTDIV1_LSB       16u

/** PRIM の POSTDIV2 のビット位置 */
#define PLL_PRIM_POSTDIV2_LSB       12u

/* ============================================================
 * CLOCKS（データシート 2.15）
 * 各クロックの供給元選択と分周。SELECTED は現在選択中の SRC を
 * ワンホットで示す（読み出し専用）。
 * ============================================================ */

/** クロック制御のベースアドレス */
#define CLOCKS_BASE                 0x40008000u

/** clk_ref 制御（SRC: bit 1:0、AUXSRC: bit 6:5） */
#define CLK_REF_CTRL                REG32(CLOCKS_BASE + 0x30u)

/** clk_ref 分周 */
#define CLK_REF_DIV                 REG32(CLOCKS_BASE + 0x34u)

/** clk_ref の選択状態（ワンホット） */
#define CLK_REF_SELECTED            REG32(CLOCKS_BASE + 0x38u)

/** clk_sys 制御（SRC: bit 0、AUXSRC: bit 7:5） */
#define CLK_SYS_CTRL                REG32(CLOCKS_BASE + 0x3Cu)

/** clk_sys 分周（bit 31:8 が整数部。0x100 で 1 分周） */
#define CLK_SYS_DIV                 REG32(CLOCKS_BASE + 0x40u)

/** clk_sys の選択状態（ワンホット） */
#define CLK_SYS_SELECTED            REG32(CLOCKS_BASE + 0x44u)

/** clk_peri 制御（AUXSRC: bit 7:5、ENABLE: bit 11） */
#define CLK_PERI_CTRL               REG32(CLOCKS_BASE + 0x48u)

/** clk_sys 復旧（resus）制御。使わないので 0 を書いて無効化する */
#define CLK_SYS_RESUS_CTRL          REG32(CLOCKS_BASE + 0x78u)

/** clk_ref の SRC マスク */
#define CLK_REF_CTRL_SRC_MASK       0x3u

/** clk_ref の SRC = XOSC */
#define CLK_REF_SRC_XOSC            0x2u

/** clk_ref SELECTED の期待値（XOSC 選択時） */
#define CLK_REF_SELECTED_XOSC       (1u << 2)

/** clk_sys の SRC マスク */
#define CLK_SYS_CTRL_SRC_MASK       0x1u

/** clk_sys の SRC = AUX（AUXSRC で選んだ源） */
#define CLK_SYS_SRC_AUX             0x1u

/** clk_sys SELECTED の期待値（clk_ref 選択時） */
#define CLK_SYS_SELECTED_REF        (1u << 0)

/** clk_sys SELECTED の期待値（AUX 選択時） */
#define CLK_SYS_SELECTED_AUX        (1u << 1)

/** clk_ref SELECTED の期待値（ROSC 選択時） */
#define CLK_REF_SELECTED_ROSC       (1u << 0)

/** AUXSRC フィールドのビット位置（clk_sys / clk_peri 共通） */
#define CLK_CTRL_AUXSRC_LSB         5u

/** AUXSRC フィールドのマスク */
#define CLK_CTRL_AUXSRC_MASK        (0x7u << CLK_CTRL_AUXSRC_LSB)

/** clk_sys の AUXSRC = PLL_SYS */
#define CLK_SYS_AUXSRC_PLL_SYS      0x0u

/** clk_peri の AUXSRC = clk_sys */
#define CLK_PERI_AUXSRC_CLK_SYS     0x0u

/** clk_peri の ENABLE ビット */
#define CLK_PERI_CTRL_ENABLE_BITS   (1u << 11)

/** CLK_SYS_DIV に書く「1 分周」の値 */
#define CLK_DIV_1                   (1u << 8)

/* --- 周波数カウンタ FC0（データシート 2.15.5） --- */

/** 基準クロック周波数[kHz] を書くレジスタ */
#define FC0_REF_KHZ                 REG32(CLOCKS_BASE + 0x80u)

/** 測定下限[kHz] */
#define FC0_MIN_KHZ                 REG32(CLOCKS_BASE + 0x84u)

/** 測定上限[kHz] */
#define FC0_MAX_KHZ                 REG32(CLOCKS_BASE + 0x88u)

/** 測定前の待ち時間 */
#define FC0_DELAY                   REG32(CLOCKS_BASE + 0x8Cu)

/** 測定時間（大きいほど高精度） */
#define FC0_INTERVAL                REG32(CLOCKS_BASE + 0x90u)

/** 測定対象クロックの選択 */
#define FC0_SRC                     REG32(CLOCKS_BASE + 0x94u)

/** 測定状態（DONE: bit 4） */
#define FC0_STATUS                  REG32(CLOCKS_BASE + 0x98u)

/** 測定結果（KHZ: bit 29:5、FRAC: bit 4:0） */
#define FC0_RESULT                  REG32(CLOCKS_BASE + 0x9Cu)

/** FC0_STATUS の DONE ビット */
#define FC0_STATUS_DONE_BITS        (1u << 4)

/** FC0_RESULT の kHz 部のビット位置（下位 5 ビットは小数部） */
#define FC0_RESULT_KHZ_LSB          5u

/** FC0_SRC: 測定停止 */
#define FC0_SRC_NONE                0x00u

/** FC0_SRC: XOSC */
#define FC0_SRC_XOSC                0x05u

/** FC0_SRC: clk_ref */
#define FC0_SRC_CLK_REF             0x08u

/** FC0_SRC: clk_sys */
#define FC0_SRC_CLK_SYS             0x09u

/** FC0_SRC: clk_peri */
#define FC0_SRC_CLK_PERI            0x0Au

/* ============================================================
 * TIMER / WATCHDOG（データシート 4.6 / 4.7）
 * TIMER は 1 マイクロ秒刻みの 64 ビットカウンタ。刻みは
 * WATCHDOG の TICK 生成器が clk_ref から作る。
 * ============================================================ */

/** タイマのベースアドレス */
#define TIMER_BASE                  0x40054000u

/** 自走カウンタ下位 32 ビット（ラッチしない読み出し） */
#define TIMER_TIMERAWL              REG32(TIMER_BASE + 0x28u)

/** ウォッチドッグのベースアドレス */
#define WATCHDOG_BASE               0x40058000u

/** TICK 生成器（CYCLES: bit 8:0、ENABLE: bit 9） */
#define WATCHDOG_TICK               REG32(WATCHDOG_BASE + 0x2Cu)

/** TICK の ENABLE ビット */
#define WATCHDOG_TICK_ENABLE_BITS   (1u << 9)

#endif /* RP2040_REGS_H */