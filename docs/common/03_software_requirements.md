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
:rationale: リングバッファサイズは8192サンプル（16KB）。1分間のトレンド判定対象期間(6000サンプル)を保持するために必要なサイズで、2のべき乗にすることでインデックス計算をビット演算で行える。RAM使用量はRP2040の264KBに対して十分小さい。

ADC+DMAドライバはADC FIFOからリングバッファへ16bit単位でDMA転送を行うこと。
DMAはring指定モードで動作し、CPU介入なしに連続的にラップアラウンドすること。
リングバッファのサイズは8192サンプルとする。
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

## SYS_002（温度の統計表示）からの派生

```{swreq} リングバッファのデータ構造
:id: SWR_007
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_002
:rationale: ハードウェア非依存の純粋なデータ構造として実装することで、ホスト側ユニットテストを可能にする（ARC_005準拠）。

リングバッファモジュールは固定長の円環状データ構造を提供すること。
バッファサイズは2の冪乗とし、要素は16bit unsigned integerとする。
ハードウェア依存の機構（レジスタアクセス等）に依存しないこと。
```

```{swreq} リングバッファのスナップショット取得
:id: SWR_008
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_002
:rationale: DMAによる書き込みが継続する中で読み出すため、完全な整合性は保証せず最大1サンプルの不整合を許容する設計。これによりロックフリーで読み出しが可能となる。

リングバッファモジュールは、現在の書き込み位置と指定したサンプル数から
過去のサンプル列をスナップショットとして取得する関数を提供すること。
読み出し中にDMAによる書き換えが発生し得るが、最大1サンプル分のデータ不整合を許容する。
```

```{swreq} 統計値の計算
:id: SWR_009
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_002
:rationale: サンプル列を入力として最大・最小・平均を出力する純粋な関数として実装。テスト容易性が高く、ハードウェア非依存。

統計モジュールは16bit unsigned integerのサンプル列を入力として、
最大値・最小値・平均値を計算する関数を提供すること。
入力サンプル数は呼び出し時に指定可能であること。
```

```{swreq} 「最新値」の定義
:id: SWR_010
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_002
:rationale: サンプリング100Hzでは1サンプルが10ms間隔となり、単一サンプルではノイズの影響を受けやすい。直近1秒分(100サンプル)の平均を取ることで読み取り値が安定する。

「最新値」は直近100サンプル（直近1秒間）の平均値として定義すること。
統計モジュールはこの「最新値」を計算する関数を提供すること。
```

```{swreq} 温度の物理変換
:id: SWR_011
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_002
:rationale: 物理変換は統計計算やリングバッファとは独立した責務であり、単体で再利用価値があるため独立モジュールとする。較正係数の差し替えにも対応しやすい。

温度変換モジュールはADC生値（12bit unsigned integer）を℃単位の浮動小数点値に変換する関数を提供すること。
RP2040内蔵温度センサのデータシートに記載された変換式を使用し、較正係数は引数またはモジュール初期化時に設定可能とすること。
```

```{swreq} 統計値の表示フォーマット
:id: SWR_012
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_002
:tbd_items: TBD-011 表示レイアウトの最終形は実機で文字幅と読みやすさを確認後に決定する。

アプリケーション層は統計値（最新値・最小値・平均値）をLCD1602（16文字×2行）に収まる形式でフォーマットすること。
温度値は摂氏で小数点以下1桁まで表示する。
```

## SYS_003（温度変化のトレンド表示）からの派生

```{swreq} トレンド判定モジュールの構成
:id: SWR_013
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_003
:rationale: トレンド判定は「時系列的な変化の検出」という、統計計算（瞬時の集計）とは異なる責務を持つため独立モジュールとする。内部では統計モジュールの平均計算を再利用する。

トレンド判定モジュールはリングバッファのサンプル列から、温度変化の傾向（上昇/下降/横ばい）を判定する関数を提供すること。
本モジュールは統計モジュールに依存して良いが、ハードウェアには依存しないこと。
```

```{swreq} 前半後半平均比較によるトレンド判定アルゴリズム
:id: SWR_014
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_003
:rationale: 始点と終点の単純比較ではノイズに弱く、線形回帰は計算負荷が高い。前半・後半の平均を比較する方式は、ノイズに対するロバスト性と実装のシンプルさのバランスが良い。

トレンド判定は以下のアルゴリズムで行うこと：
1. 直近1分間（6000サンプル）を前半30秒（3000サンプル）と後半30秒（3000サンプル）に分割する
2. 前半の平均温度と後半の平均温度をそれぞれ計算する
3. 後半平均から前半平均を減じた差分を求める
4. 差分が閾値を超えるかで上昇/下降/横ばいを判定する
```

```{swreq} トレンド判定の閾値
:id: SWR_015
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_003
:rationale: 室温の自然変動は通常数分単位で0.5℃程度。0.3℃の閾値は短時間の変化を検出しつつ、ノイズや微小変動を「横ばい」として扱うバランス点。
:tbd_items: TBD-012 閾値0.3℃は仮置き、実機での室温変動の観察結果に基づき調整する。

差分の絶対値が0.3℃を超え、かつ正の値であれば上昇傾向、
負の値であれば下降傾向、絶対値が0.3℃以下であれば横ばいと判定すること。
```

```{swreq} トレンド判定の実行周期
:id: SWR_016
:status: draft
:type_kind: Timing
:layer: application
:refines: SYS_003
:rationale: LCD表示更新と同じ周期にすることで、計算結果と表示が同期する。トレンドは緩やかに変化するため500ms周期での判定で十分。

アプリケーション層はLCD表示更新と同じ500ms周期でトレンド判定を実行し、結果を表示に反映すること。
```

```{swreq} トレンドの表示記号
:id: SWR_017
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_003
:tbd_items: TBD-013 表示記号の最終形は実機で文字幅と視認性を確認後に決定する。LCD1602のカスタム文字機能による上下矢印作成も検討する。

アプリケーション層はトレンド判定の結果をLCD1602に記号で表示すること。
記号の暫定案：上昇は「↑」または「+」、下降は「↓」または「-」、横ばいは「-」または「=」とする。
記号はSWR_012の表示フォーマットに組み込まれる。
```
