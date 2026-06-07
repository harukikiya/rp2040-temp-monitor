/*
 * Copyright (c) 2021 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*
 * SSI（SPI master）の通信完了を待つヘルパールーチン。
 *
 * 本プロジェクトの no-SDK 方針に合わせ、pico-sdk への依存を排除している。
 * 使用するレジスタ定数（SSI_SR_OFFSET、SSI_SR_TFE_BITS、SSI_SR_BUSY_BITS）は、
 * このファイルを #include する boot2 本体が rp2040_boot_regs.h を取り込んでいる
 * 前提で解決される。
 *
 * 前提：r3 に XIP_SSI_BASE（SSI レジスタのベースアドレス）が入っていること。
 */

#ifndef _BOOT2_HELPER_WAIT_SSI_READY
#define _BOOT2_HELPER_WAIT_SSI_READY

wait_ssi_ready:
    push {r0, r1, lr}

    // コマンドの完了条件：送信すべきものが残っておらず（TX FIFO が空）、
    // かつ SSI がビジーでない（CSn が解除された）状態。
    // Command is complete when there is nothing left to send
    // (TX FIFO empty) and SSI is no longer busy (CSn deasserted)
1:
    ldr r1, [r3, #SSI_SR_OFFSET]    // ステータスレジスタを読む
    movs r0, #SSI_SR_TFE_BITS       // TX FIFO Empty ビット
    tst r1, r0
    beq 1b                          // TFE が立つまで待つ
    movs r0, #SSI_SR_BUSY_BITS       // BUSY ビット
    tst r1, r0
    bne 1b                          // BUSY が下りるまで待つ

    pop {r0, r1, pc}

#endif
