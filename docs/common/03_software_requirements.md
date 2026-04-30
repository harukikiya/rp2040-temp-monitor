# ソフトウェア要件

本書では、システム要件から派生するソフトウェア要件を、レイヤごとに整理して記述する。
各要件は属するレイヤを`layer`属性で示す。

## SYS_001（温度の継続的変化可視化）からの派生

```{swreq} ADC初期化と温度センサチャネル選択
:id: SWR_001
:status: draft
:type_kind: Functional
:layer: driver
:refines: SYS_001

ADCドライバはRP2040のADCを初期化し、内蔵温度センサ（ADCチャネル4）を入力として選択すること。
温度センサのバイアスを有効化すること。
```

```{swreq} ADC+DMAによる自動サンプリング
:id: SWR_002
:status: draft
:type_kind: Functional
:layer: driver
:refines: SYS_001
:tbd_items: TBD-009 DMAリングサイズの仮置きは128サンプル（2の冪乗）、メモリ使用量と保持期間のバランスで最終決定する。

ADC+DMAドライバはADC FIFOからリングバッファへ16bit単位でDMA転送を行うこと。
DMAはring指定モードで動作し、CPU介入なしに連続的にラップアラウンドすること。
```

```{swreq} ハードウェアタイマーによるサンプリングトリガ
:id: SWR_003
:status: draft
:type_kind: Timing
:layer: hal
:refines: SYS_001

Timer HALはADCのサンプリングを100Hz周期（10ms間隔）でトリガすること。
トリガはハードウェアタイマー経由で行い、ソフトウェアによるポーリングは行わないこと。
```

```{swreq} I2Cバスの初期化
:id: SWR_004
:status: draft
:type_kind: Functional
:layer: driver
:refines: SYS_001
:tbd_items: TBD-010 I2C速度は仮置きで100kHz、LCDの応答性を確認後に決定。

I2C HALはRP2040のI2C0を100kHzのマスタモードで初期化すること。
GPIO割り当ては実装段階で確定するが、内蔵プルアップを使用する前提とする。
```

```{swreq} LCD1602の初期化
:id: SWR_005
:status: draft
:type_kind: Functional
:layer: driver
:refines: SYS_001

LCDドライバはPCF8574経由でLCD1602を4ビットモードで初期化すること。
HD44780の初期化シーケンスに準拠し、必要なディレイを遵守すること。
```

```{swreq} 表示更新の周期制御
:id: SWR_006
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_001

アプリケーション層は500ms周期でLCD表示を更新すること。
500ms未満の周期での更新を行わないこと（LCD表示のチラつき防止）。
```
