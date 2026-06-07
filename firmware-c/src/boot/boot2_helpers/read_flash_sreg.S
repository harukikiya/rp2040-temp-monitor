/*
 * Copyright (c) 2021 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*
 * フラッシュのステータスレジスタを読み出すヘルパールーチン。
 *
 * 本プロジェクトの no-SDK 方針に合わせ、pico-sdk への依存を排除している。
 * 使用するレジスタ定数（SSI_DR0_OFFSET）は、このファイルを #include する
 * boot2 本体が rp2040_boot_regs.h を取り込んでいる前提で解決される。
 *
 * 前提：r3 に XIP_SSI_BASE が入っていること。
 * 引数：r0 にステータス読み出しコマンドを渡す。
 * 戻り値：r0 にステータス値を返す。
 */

#ifndef _BOOT2_HELPER_READ_FLASH_SREG
#define _BOOT2_HELPER_READ_FLASH_SREG

// wait_ssi_ready を利用するため取り込む（自前パス）
#include "boot2_helpers/wait_ssi_ready.S"

// Pass status read cmd into r0.
// Returns status value in r0.
.global read_flash_sreg
.type read_flash_sreg,%function
.thumb_func
read_flash_sreg:
    push {r1, lr}
    str r0, [r3, #SSI_DR0_OFFSET]   // コマンドを送信
    // ダミーバイト（応答を読むためにクロックを出す）
    // Dummy byte:
    str r0, [r3, #SSI_DR0_OFFSET]

    bl wait_ssi_ready               // 送受信完了を待つ
    // 最初のバイト（コマンドエコー）を捨て、次のバイトを取得
    // Discard first byte and combine the next two
    ldr r0, [r3, #SSI_DR0_OFFSET]
    ldr r0, [r3, #SSI_DR0_OFFSET]

    pop {r1, pc}

#endif
