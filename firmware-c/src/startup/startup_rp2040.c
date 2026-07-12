/**
 * @file startup_rp2040.c
 * @brief crt0（ベクタテーブル + リセットハンドラ）。
 * 
 * @details
 * リセット直後に最初に実行される起動コード。ベクタテーブルを @c .vectors
 * （フラッシュ 0x10000100）に配置し、Reset_Handler で C 実行環境を整えてから
 * main() を呼ぶ。
 * 
 * 起動の前提（boot2 が済ませていること）：
 * RP2040 のブート ROM が boot2 を実行し、boot2 が XIP を有効化したうえで VTOR に
 * ベクタテーブル位置（0x10000100）を設定し、ベクタ表 [0] を初期 SP にロードして
 * [1]=Reset_Handler へ分岐する。したがって本ファイルの Reset_Handler で VTOR を
 * 設定する必要はない。
 * 
 * @note SystemInit / クロック初期化は 2-D-3 で追加する。
 * @note boot2（チェックサム済み）との最終フラッシュイメージ統合は 2-D-1 で行う。
 * @note 命名は CMSIS（startup_ARMCM0plus.c）に準拠する。
 * 
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdint.h>

/**
 * @name リンカ供給シンボル
 * @brief リンカスクリプト rp2040.ld が定義する。いずれもアドレスとしてのみ扱う
 *        （型は便宜上 uint32_t）。
 * @{
 */
extern uint32_t __StackTop;     /**< スタック最上位 = 初期 SP */
extern uint32_t __etext;        /**< .data 初期値の格納先（LMA, フラッシュ） */
extern uint32_t __data_start__; /**< .data 開始（VMA, RAM） */
extern uint32_t __data_end__;   /**< .data 終了（VMA, RAM） */
extern uint32_t __bss_start__;  /**< .bss 開始 */
extern uint32_t __bss_end__;    /**< .bss 終了 */
/** @} */

/** @brief アプリケーション本体（src/main.c）。 */
extern int main(void);

/* 起動コード本体（実体はファイル下部で定義） */
void Reset_Handler(void);
void Default_Handler(void);

/**
 * @def ALIAS
 * @brief ハンドラを weak 化し Default_Handler にエイリアスする。
 * @param f エイリアス先の関数名。
 * @details ユーザが同名の関数を実装すると、そちらが優先されて置き換わる。
 */
#define ALIAS(f) __attribute__((weak, alias(#f)))

/**
 * @name システム例外ハンドラ
 * @brief 既定では Default_Handler にエイリアスされる weak シンボル。
 * @{
 */
void NMI_Handler(void)          ALIAS(Default_Handler);
void HardFault_Handler(void)    ALIAS(Default_Handler);
void SVC_Handler(void)          ALIAS(Default_Handler);
void PendSV_Handler(void)       ALIAS(Default_Handler);
void SysTick_Handler(void)      ALIAS(Default_Handler);
/** @} */

/**
 * @name RP2040 外部割り込みハンドラ
 * @brief IRQ0..IRQ25 が実使用、IRQ26..31 は未使用（予約）。
 *        いずれも既定では Default_Handler にエイリアスされる weak シンボル。
 * @{
 */
void TIMER_IRQ_0_Handler(void)   ALIAS(Default_Handler);
void TIMER_IRQ_1_Handler(void)   ALIAS(Default_Handler);
void TIMER_IRQ_2_Handler(void)   ALIAS(Default_Handler);
void TIMER_IRQ_3_Handler(void)   ALIAS(Default_Handler);
void PWM_IRQ_WRAP_Handler(void)  ALIAS(Default_Handler);
void USBCTRL_IRQ_Handler(void)   ALIAS(Default_Handler);
void XIP_IRQ_Handler(void)       ALIAS(Default_Handler);
void PIO0_IRQ_0_Handler(void)    ALIAS(Default_Handler);
void PIO0_IRQ_1_Handler(void)    ALIAS(Default_Handler);
void PIO1_IRQ_0_Handler(void)    ALIAS(Default_Handler);
void PIO1_IRQ_1_Handler(void)    ALIAS(Default_Handler);
void DMA_IRQ_0_Handler(void)     ALIAS(Default_Handler);
void DMA_IRQ_1_Handler(void)     ALIAS(Default_Handler);
void IO_IRQ_BANK0_Handler(void)  ALIAS(Default_Handler);
void IO_IRQ_QSPI_Handler(void)   ALIAS(Default_Handler);
void SIO_IRQ_PROC0_Handler(void) ALIAS(Default_Handler);
void SIO_IRQ_PROC1_Handler(void) ALIAS(Default_Handler);
void CLOCKS_IRQ_Handler(void)    ALIAS(Default_Handler);
void SPI0_IRQ_Handler(void)      ALIAS(Default_Handler);
void SPI1_IRQ_Handler(void)      ALIAS(Default_Handler);
void UART0_IRQ_Handler(void)     ALIAS(Default_Handler);
void UART1_IRQ_Handler(void)     ALIAS(Default_Handler);
void ADC_IRQ_FIFO_Handler(void)  ALIAS(Default_Handler);
void I2C0_IRQ_Handler(void)      ALIAS(Default_Handler);
void I2C1_IRQ_Handler(void)      ALIAS(Default_Handler);
void RTC_IRQ_Handler(void)       ALIAS(Default_Handler);
/** @} */

/** @brief ベクタテーブルの1エントリ（関数ポインタ）の型。 */
typedef void (*vector_t)(void);

/**
 * @brief ベクタテーブル（@c .vectors, フラッシュ 0x10000100）。
 * 
 * @details
 * 全 48 エントリ = システム例外 16 + 外部 IRQ 32。
 * - [0]        初期スタックポインタ（__StackTop）
 * - [1]        Reset
 * - [2..15]    システム例外（M0+ にないものは予約 = 0）
 * - [16..47]   外部 IRQ（RP2040：IRQ0..25 が実使用、26..31 は未使用）
 * 
 * @note @c used 属性で --gc-sections による削除を防ぐ（CPU がアドレスで参照するため）。
 * @note [0] は SP 値であり関数ではないが、表の型に合わせて関数ポインタへキャストする
 *          （CMSIS と同じ手法。
 */
__attribute__((used, section(".vectors")))
const vector_t __VECTOR_TABLE[48] = {
    (vector_t)(&__StackTop),    /*  0：初期スタックポインタ */
    Reset_Handler,              /*  1：Reset */
    NMI_Handler,                /*  2：NMI */
    HardFault_Handler,          /*  3：HardFault */
    0,                          /*  4：予約（M0+ は MemManage 専用ベクタ無し→HardFault 集約） */
    0,                          /*  5：予約（M0+ は BusFault 専用ベクタ無し→HardFault 集約） */
    0,                          /*  6：予約（M0+ は UsageFault 専用ベクタ無し→HardFault 集約） */
    0,                          /*  7：予約 */
    0,                          /*  8：予約 */
    0,                          /*  9：予約 */
    0,                          /* 10：予約 */
    SVC_Handler,                /* 11：SVCall */
    0,                          /* 12：予約（DebugMon 無し） */
    0,                          /* 13：予約 */
    PendSV_Handler,             /* 14：PendSV */
    SysTick_Handler,            /* 15：SysTick */
    TIMER_IRQ_0_Handler,        /* 16：IRQ0  TIMER_IRQ_0 */
    TIMER_IRQ_1_Handler,        /* 17: IRQ1  TIMER_IRQ_1 */
    TIMER_IRQ_2_Handler,        /* 18: IRQ2  TIMER_IRQ_2 */
    TIMER_IRQ_3_Handler,        /* 19: IRQ3  TIMER_IRQ_3 */
    PWM_IRQ_WRAP_Handler,       /* 20: IRQ4  PWM_IRQ_WRAP */
    USBCTRL_IRQ_Handler,        /* 21: IRQ5  USBCTRL_IRQ */
    XIP_IRQ_Handler,            /* 22: IRQ6  XIP_IRQ */
    PIO0_IRQ_0_Handler,         /* 23: IRQ7  PIO0_IRQ_0 */
    PIO0_IRQ_1_Handler,         /* 24: IRQ8  PIO0_IRQ_1 */
    PIO1_IRQ_0_Handler,         /* 25: IRQ9  PIO1_IRQ_0 */
    PIO1_IRQ_1_Handler,         /* 26: IRQ10 PIO1_IRQ_1 */
    DMA_IRQ_0_Handler,          /* 27: IRQ11 DMA_IRQ_0 */
    DMA_IRQ_1_Handler,          /* 28: IRQ12 DMA_IRQ_1 */
    IO_IRQ_BANK0_Handler,       /* 29: IRQ13 IO_IRQ_BANK0 */
    IO_IRQ_QSPI_Handler,        /* 30: IRQ14 IO_IRQ_QSPI */
    SIO_IRQ_PROC0_Handler,      /* 31: IRQ15 SIO_IRQ_PROC0 */
    SIO_IRQ_PROC1_Handler,      /* 32: IRQ16 SIO_IRQ_PROC1 */
    CLOCKS_IRQ_Handler,         /* 33: IRQ17 CLOCKS_IRQ */
    SPI0_IRQ_Handler,           /* 34: IRQ18 SPI0_IRQ */
    SPI1_IRQ_Handler,           /* 35: IRQ19 SPI1_IRQ */
    UART0_IRQ_Handler,          /* 36: IRQ20 UART0_IRQ */
    UART1_IRQ_Handler,          /* 37: IRQ21 UART1_IRQ */
    ADC_IRQ_FIFO_Handler,       /* 38: IRQ22 ADC_IRQ_FIFO */
    I2C0_IRQ_Handler,           /* 39: IRQ23 I2C0_IRQ */
    I2C1_IRQ_Handler,           /* 40: IRQ24 I2C1_IRQ */
    RTC_IRQ_Handler,            /* 41: IRQ25 RTC_IRQ */
    Default_Handler,            /* 42: IRQ26（未使用） */
    Default_Handler,            /* 43: IRQ27（未使用） */
    Default_Handler,            /* 44: IRQ28（未使用） */
    Default_Handler,            /* 45: IRQ29（未使用） */
    Default_Handler,            /* 46: IRQ30（未使用） */
    Default_Handler,            /* 47: IRQ31（未使用） */
};

/**
 * @brief リセットハンドラ。C 実行環境を整えてから main() を呼ぶ。
 * 
 * @details
 * @c .data を LMA（フラッシュ上の初期値） から VMA（RAM） へコピーし、@c .bss を 0 で
 * 初期化したのち main() を呼ぶ。実行時点でスタックは boot2 が __StackTop に設定済み
 * なので、ローカル変数を使用できる。VTOR は boot2 が設定済みのため、ここでは触らない。
 * 各範囲が空（該当グローバルが無い）なら、コピー/ゼロ初期化は何もしない。
 */
void Reset_Handler(void)
{
    /* .data を LMA から VMA へコピーする */
    const uint32_t *src = &__etext;
    uint32_t *dst = &__data_start__;
    while (dst < &__data_end__) {
        *dst++ = *src++;
    }

    /* .bss を 0 で初期化する */
    for (dst = &__bss_start__; dst < &__bss_end__; ) {
        *dst++ = 0u;
    }

    /* アプリケーション本体へ */
    (void)main();

    /* main から戻ってきた場合の保険。組み込みでは通常戻らない。 */
    for (;;) {
    }
}

/**
 * @brief 既定ハンドラ。未実装の例外/割り込みで停止する。
 * 
 * @details
 * 無限ループに入って停止する。デバッガで停止位置（このアドレス）を見れば、
 * 想定外の割り込みが起きたことを検知できる。
 */
void Default_Handler(void)
{
    for (;;) {
    }
}
