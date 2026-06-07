/**
 * @file rp2040_boot_regs.h
 * @brief boot2 が使用する RP2040 レジスタ定義（アセンブリ用）
 *
 * @details
 * boot2_w25q080.S が必要とする最小限のレジスタ定数を、アセンブリから直接
 * 使える形（素の数値）で定義する。pico-sdk の hardware/regs/*.h への依存を
 * 排除するために、本プロジェクトで自前で用意したもの。
 *
 * CMSIS スタイルの RP2040.h（generated/RP2040.h）は構造体ベースで、レジスタ
 * オフセット定数を持たず、また `_Pos`/`_Msk` 命名のため、アセンブリの
 * boot2 からは利用しづらい。そこで boot2 が使う定数のみを本ファイルに集約する。
 *
 * 各値の出典：pico-sdk の hardware/regs/ssi.h、pads_qspi.h、addressmap.h。
 * RP2040 データシート Section 4.10（SSI）、Section 2.19（PADS_QSPI）も参照。
 *
 * @note アセンブリ専用。C からは include しない想定。
 *       pico-sdk の `_u(...)` マクロは使わず、素の 16 進数で定義している。
 *
 * @see RP2040 datasheet Section 4.10 SSI
 * @see RP2040 datasheet Section 2.19 GPIO (PADS_QSPI)
 *
 * @copyright SPDX-License-Identifier: BSD-3-Clause
 */

#ifndef RP2040_BOOT_REGS_H
#define RP2040_BOOT_REGS_H

/* ============================================================
 * ベースアドレス（addressmap.h 由来）
 * ============================================================ */

/** QSPI パッド制御レジスタのベースアドレス */
#define PADS_QSPI_BASE  0x40020000

/** SSI（SPI master）レジスタのベースアドレス */
#define XIP_SSI_BASE    0x18000000

/** XIP 領域（フラッシュ実行領域）のベースアドレス */
#define XIP_BASE        0x10000000

/* ============================================================
 * PADS_QSPI レジスタ（pads_qspi.h 由来）
 * QSPI ピンの電気的特性（駆動電流、スルーレート、シュミットトリガ）を制御する
 * ============================================================ */

/** SCLK パッド制御レジスタのオフセット */
#define PADS_QSPI_GPIO_QSPI_SCLK_OFFSET        0x00000004
/** SCLK 駆動電流（DRIVE）フィールドのビット位置 */
#define PADS_QSPI_GPIO_QSPI_SCLK_DRIVE_LSB     4
/** SCLK スルーレート高速化（SLEWFAST）ビットのマスク */
#define PADS_QSPI_GPIO_QSPI_SCLK_SLEWFAST_BITS 0x00000001

/** SD0 パッド制御レジスタのオフセット */
#define PADS_QSPI_GPIO_QSPI_SD0_OFFSET         0x00000008
/** SD1 パッド制御レジスタのオフセット */
#define PADS_QSPI_GPIO_QSPI_SD1_OFFSET         0x0000000c
/** SD2 パッド制御レジスタのオフセット */
#define PADS_QSPI_GPIO_QSPI_SD2_OFFSET         0x00000010
/** SD3 パッド制御レジスタのオフセット */
#define PADS_QSPI_GPIO_QSPI_SD3_OFFSET         0x00000014

/** SD0 シュミットトリガ（SCHMITT）ビットのマスク（入力遅延削減のため解除する） */
#define PADS_QSPI_GPIO_QSPI_SD0_SCHMITT_BITS   0x00000002

/* ============================================================
 * SSI レジスタオフセット（ssi.h 由来）
 * SSI = Synchronous Serial Interface（RP2040 の SPI master）
 * ============================================================ */

/** コントロールレジスタ 0（フレームフォーマット、転送モード等） */
#define SSI_CTRLR0_OFFSET          0x00000000
/** コントロールレジスタ 1（データフレーム数 NDF） */
#define SSI_CTRLR1_OFFSET          0x00000004
/** SSI 有効化レジスタ（SSI_EN） */
#define SSI_SSIENR_OFFSET          0x00000008
/** ボーレートレジスタ（SPI クロック分周比） */
#define SSI_BAUDR_OFFSET           0x00000014
/** ステータスレジスタ（TFE、BUSY 等） */
#define SSI_SR_OFFSET              0x00000028
/** データレジスタ 0（TX/RX FIFO） */
#define SSI_DR0_OFFSET             0x00000060
/** RX サンプル遅延レジスタ */
#define SSI_RX_SAMPLE_DLY_OFFSET   0x000000f0
/** SPI 専用コントロールレジスタ 0（Quad モード詳細制御） */
#define SSI_SPI_CTRLR0_OFFSET      0x000000f4

/* ============================================================
 * SSI_CTRLR0 ビットフィールド（ssi.h 由来）
 * ============================================================ */

/** SPI フレームフォーマット（FRF）のビット位置 */
#define SSI_CTRLR0_SPI_FRF_LSB             21
/** FRF = Quad I/O モードの値 */
#define SSI_CTRLR0_SPI_FRF_VALUE_QUAD      0x2
/** データフレームサイズ（DFS_32）のビット位置 */
#define SSI_CTRLR0_DFS_32_LSB              16
/** 転送モード（TMOD）のビット位置 */
#define SSI_CTRLR0_TMOD_LSB                8
/** TMOD = 送受信両方（TX and RX）の値 */
#define SSI_CTRLR0_TMOD_VALUE_TX_AND_RX    0x0
/** TMOD = EEPROM Read（命令/アドレス送信後にデータ受信）の値 */
#define SSI_CTRLR0_TMOD_VALUE_EEPROM_READ  0x3

/* ============================================================
 * SSI_SPI_CTRLR0 ビットフィールド（ssi.h 由来）
 * ============================================================ */

/** XIP 時に送るコマンド（XIP_CMD）のビット位置 */
#define SSI_SPI_CTRLR0_XIP_CMD_LSB             24
/** アドレス送信後の待機サイクル数（WAIT_CYCLES）のビット位置 */
#define SSI_SPI_CTRLR0_WAIT_CYCLES_LSB         11
/** 命令長（INST_L）のビット位置 */
#define SSI_SPI_CTRLR0_INST_L_LSB              8
/** INST_L = 命令なし（NONE）の値 */
#define SSI_SPI_CTRLR0_INST_L_VALUE_NONE       0x0
/** INST_L = 8 ビット命令の値 */
#define SSI_SPI_CTRLR0_INST_L_VALUE_8B         0x2
/** アドレス長（ADDR_L）のビット位置 */
#define SSI_SPI_CTRLR0_ADDR_L_LSB              2
/** 転送タイプ（TRANS_TYPE）のビット位置 */
#define SSI_SPI_CTRLR0_TRANS_TYPE_LSB          0
/** TRANS_TYPE = 命令 Serial／アドレス Quad（1C2A）の値 */
#define SSI_SPI_CTRLR0_TRANS_TYPE_VALUE_1C2A   0x1
/** TRANS_TYPE = 命令・アドレスとも Quad（2C2A）の値 */
#define SSI_SPI_CTRLR0_TRANS_TYPE_VALUE_2C2A   0x2

/* ============================================================
 * SSI_SR（ステータスレジスタ）ビット（ssi.h 由来）
 * ============================================================ */

/** TX FIFO Empty（TFE）ビットのマスク */
#define SSI_SR_TFE_BITS    0x00000004
/** SSI Busy（BUSY）ビットのマスク */
#define SSI_SR_BUSY_BITS   0x00000001

/* ============================================================
 * M0PLUS / PPB（addressmap.h、m0plus.h 由来）
 * Cortex-M0+ のシステム制御レジスタ。boot2 の最後に、ベクタテーブルの
 * 位置を VTOR に設定してリセットハンドラへジャンプする際に使う。
 * ============================================================ */

/** Private Peripheral Bus のベースアドレス（Cortex-M のシステムレジスタ領域、ARM 固定） */
#define PPB_BASE              0xe0000000

/** VTOR（Vector Table Offset Register）の PPB ベースからのオフセット */
#define M0PLUS_VTOR_OFFSET    0x0000ed08

#endif /* RP2040_BOOT_REGS_H */
