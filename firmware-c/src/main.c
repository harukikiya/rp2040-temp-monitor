/**
 * @file main.c
 * @brief オンボード LED（GPIO25）を点滅させる。
 * 
 * @details
 * 段階 2-D-2。自前の boot2 + crt0 で起動し、SDK を使わずに GPIO を直接叩いて
 * LED を点滅させる。ここまでに作った boot2（CRC 付き）・リンカスクリプト・crt0 が
 * 実機で正しく動くことを、初めて目視で確認するための最小プログラム。
 * 
 * 手順：
 *      1. IO_BANK0 と PADS_BANK0 のリセットを解除する
 *      2. GPIO25 の機能を SIO（F5）に設定する
 *      3. GPIO25 を出力する
 *      4. 出力を反転しながら遅延ループを回す
 * 
 * @note クロックはまだ初期化していないため、システムクロックは ROSC（約 6.5 MHz、個体差あり）で動作する。
 *       したがって点滅周期は不正確である。正確な時間制御は段階 2-D-3 でクロックを初期化してから扱う。
 * 
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdint.h>

#include "rp2040_regs.h"

/** @brief オンボード LED が接続された GPIO 番号。 */
#define LED_PIN             25u

/** @brief LED のビットマスク。 */
#define LED_MASK            (1u << LED_PIN)

/**
 * @brief 遅延ループの反復回数。
 * @details ROSC（約 6.5 MHz）と最適化なしのビルドを前提に、点滅が目視できる程度
 *          （半周期およそ 0.3 秒）を狙った概算値。正確な時間ではない。
 */
#define DELAY_LOOPS         200000u

/**
 * @brief IO_BANK0 と PAD_BANK0 のリセットを解除する。
 * 
 * @details
 * RP2040 はリセット直後、ほとんどのペリフェラルがリセット状態にある。
 * RESET レジスタの該当ビットを 0 にして解除し、RESET_DONE で完了を待つ。
 * 待たずにレジスタへ書くと設定が失われる。
 */
static void gpio_reset_release(void)
{
    const uint32_t mask = RESETS_IO_BANK0_BITS | RESETS_PADS_BANK0_BITS;

    RESETS_RESET &= ~mask;
    while ((RESETS_RESET_DONE & mask) != mask) {
        /* 解除完了を待つ */
    }
}

/**
 * @brief LED 用に GPIO25 を出力として初期化する。
 * 
 * @details
 * 機能選択を SIO にしたうえで、SIO の GPIO_OE_SET で出力を有効化する。
 * 初期状態は消灯（GPIO_OUT_CLR）とする。
 * SIO は SET/CLR/XOR 専用レジスタを持ち、読み出し・変更・書き戻しをせずに単一ビットを操作できる。
 */
static void led_init(void)
{
    IO_BANK0_GPIO_CTRL(LED_PIN) = IO_BANK0_FUNCSEL_SIO;

    SIO_GPIO_OE_SET     = LED_MASK;
    SIO_GPIO_OUT_CLR    = LED_MASK;
}

/**
 * @brief 概算の遅延を行う。
 * 
 * @details
 * タイマをまだ使わないため、単純な減算ループで時間を潰す。
 * 引数を volatile にすることで、最適化が有効な場合でもループが削除されないようにする。
 * 
 * @param count ループ回数。
 */
static void delay_loop(volatile uint32_t count)
{
    while (count > 0u) {
        count--;
    }
}

/**
 * @brief アプリケーションのエントリポイント。
 * 
 * @details GPIO を初期化し、LED を点滅させ続ける。組み込みのため戻らない。
 * 
 * @return int 形式上の戻り値（実際には戻らない）。
 */
int main(void)
{
    gpio_reset_release();
    led_init();

    for (;;) {
        SIO_GPIO_OUT_XOR = LED_MASK;
        delay_loop(DELAY_LOOPS);
    }
}
