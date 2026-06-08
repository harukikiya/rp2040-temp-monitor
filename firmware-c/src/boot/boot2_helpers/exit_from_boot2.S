/*
 * Copyright (c) 2021 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*
 * boot2 から本体（ステージ3＝ユーザーファームウェア）へ抜けるヘルパールーチン。
 *
 * 本プロジェクトの no-SDK 方針に合わせ、pico-sdk への依存を排除している。
 * 元は #include "hardware/regs/m0plus.h" で M0PLUS_VTOR_OFFSET を、
 * addressmap.h で PPB_BASE / XIP_BASE を取り込んでいたが、これらは
 * boot2 本体が取り込む rp2040_boot_regs.h で定義されている前提で解決される。
 *
 * 動作：
 *  - bootrom から来た場合、（事前に push した）lr が 0 になっており、
 *    フラッシュイメージ先頭のベクタテーブルを経由して起動する。
 *  - 通常の関数呼び出しから来た場合は lr が非ゼロなので、その値へ戻る。
 */

#ifndef _BOOT2_HELPER_EXIT_FROM_BOOT2
#define _BOOT2_HELPER_EXIT_FROM_BOOT2

// If entered from the bootrom, lr (which we earlier pushed) will be 0,
// and we vector through the table at the start of the main flash image.
// Any regular function call will have a nonzero value for lr.
check_return:
    pop {r0}
    cmp r0, #0
    beq vector_into_flash           // lr == 0：bootrom から来た → ベクタテーブル経由で起動
    bx r0                           // lr != 0：通常の呼び出し → 呼び出し元へ戻る
vector_into_flash:
    // フラッシュ先頭 +0x100（boot2 の 256 バイト直後）にベクタテーブルがある。
    ldr r0, =(XIP_BASE + 0x100)
    // VTOR（Vector Table Offset Register）にベクタテーブルの位置を設定する。
    ldr r1, =(PPB_BASE + M0PLUS_VTOR_OFFSET)
    str r0, [r1]
    // ベクタテーブルの先頭 2 ワード（初期 SP、リセットハンドラ）を読み込む。
    ldmia r0, {r0, r1}
    msr msp, r0                     // 初期スタックポインタを設定
    bx r1                           // リセットハンドラへジャンプ

#endif
