/**
 * @file main.c
 * @brief アプリケーションのエントリ（スタブ）。
 * 
 * @details
 * 現段階（2-C-4）ではスタブ。crt0 の Reset_Handler から呼ばれる。
 * 実処理（LED 点滅など）は段階 2-D-2 以降で実装する。
 * 
 * SPDX-License-Identifier: BSD-3-Clause
 */

/**
 * @brief アプリケーションのエントリポイント
 * 
 * @details
 * 現段階では何もせず無限ループする。実処理は後続段階で追加する。
 * 組み込みのため通常は戻らない。
 * 
 * @return int 形式上の戻り値（実際には戻らない）。
 */
int main(void)
{
    for (;;) {
        /* 何もしない。実処理は後続段階で追加する。 */
    }
}
