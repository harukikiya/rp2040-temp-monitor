/* 
 * linker_probe.c - リンカスクリプト rp2040.ld の静的検証用プローブ
 * 
 * SPDX-License-Identifier: BSD-3-Clause
 * 
 * 目的:
 *      crt0（段階2-C-4）実装前に、リンカスクリプトが意図通りのELFを生成するかを
 *      静的検証するための最小入力。各セクション（.data / .bss / .vectors / .text）に
 *      データを配置し、readelf / objdump / nm でセクション配置・LMA / VMA・シンボル定義
 *      を確認できるようにする。
 * 
 * 位置づけ:
 *      firmware-c/verify/ はリンカ/ビルドの静的検証専用。将来のユニットテスト（test/）
 *      とは責務を分ける。本ファイルは crt0 実装後に実物へ差し替えられる暫定物であり、実機では使用しない。
 */

#include <stdint.h>

/* 
 * .data セクションの検証用。
 * 初期値を持つグローバル変数は .data に置かれる。
 * リンカスクリプトの `.data : { ... } > RAM AT> FLASH` により、
 * VMA（実行時アドレス） = RAM、LMA（初期値の格納位置） = FLASH に
 * 分離されること objdump -h で確認するためのデータ。
 * volatile は最適化による除去を防ぐため。
 */
volatile uint32_t probe_data = 0xABCD1234;

/* 
 * .bss セクションの検証用。
 * 初期値を持たない（またはゼロ初期化される）グローバル変数は .bss に置かれる。
 * .bss は（NOLOAD）のためフラッシュ上に実体を持たず、
 * __bss_start__ / __bss_end__ の範囲に入ることを確認する。
 */
volatile uint32_t probe_bss;

/* 
 * .vectors セクションの検証用（ベクタテーブルのダミー）。
 * 本物のベクタテーブルは crt0（2-C-4）で定義するが、本段階では
 * .vectors が 0x10000100 に正しく配置されるかの「配置確認」のために
 * ダミーの2ワードを置く。
 *      [0] = 初期スタックポインタ相当（__StackTop = 0x20042000 を想定した仮値）
 *      [1] = リセットベクタ相当（末尾ビット1 = Thumbビット。M0+はThumbのみ）
 * 注意：これらの「値の正しさ」は実物の crt0 が入る2-C-4で検証する。
 *      本段階で見るのは .vectors の配置位置のみ。
 */
__attribute__((used, section(".vectors")))
const uint32_t probe_vectors[2] = {
    0x20042000u,    /* 初期SP相当（仮値） */
    0x10000101u,    /* Reset_Handler相当（仮値、Thumbビット付き） */
};

/* 
 * .text セクションおよび ENTRY(Reset_Handler) の検証用。
 * リンカスクリプトは ENTRY(Reset_Handler) を想定しているため、
 * Reset_Handler シンボルが存在しないとリンク時に
 * `cannot find entry symbol Reset_Handler` 警告が出る。
 * ダミー実体を置くことで警告を解消し、警告ゼロでリンク成立を確認する。
 * 本物の Reset_Handler は crt0（2-C-4）で実装する。
 */
void Reset_Handler(void)
{
    for (;;) {
        /* 何もしない無限ループ（検証用ダミー） */
    }
}
