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
:rationale: 統合ADC+DMAドライバとする判断の経緯はADR-0001参照。

ADCドライバはRP2040のADCを初期化し、内蔵温度センサ（ADCチャネル4）を入力として選択すること。
温度センサのバイアスを有効化すること。
```

```{swreq} ADC+DMAによる自動サンプリング
:id: SWR_002
:status: draft
:type_kind: Functional
:layer: driver
:refines: SYS_001
:rationale: リングバッファサイズは8192サンプル(16KB)。1分間のトレンド判定対象期間(6000サンプル)を保持するために必要なサイズで、2のべき乗にすることでインデックス計算をビット演算で行える。RAM使用量はRP2040の264KBに対して十分小さい。統合ADC+DMAドライバとする判断はADR-0001参照。

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
:rationale: DMAによる書き込みが継続する中で読み出すため、完全な整合性は保証せず最大1サンプルの不整合を許容する設計。これによりロックフリーで読み出しが可能となる。本不整合許容と SYS_005 の整合性保証は別データ(リングバッファ vs 計算結果)を対象としており両立する。詳細はADR-0002参照。

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

## SYS_004（コア分散）からの派生

```{swreq} Core0の責務
:id: SWR_018
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_004
:rationale: I/O形処理（ADCサンプリング、LCD表示）はハードウェアアクセスが集中するため同一コアにまとめる。これによりI/O系の応答時間が予測可能となり、ハードウェアエラー時の挙動も追跡しやすくなる。

Core0は以下の責務を持つこと:
- ADC+DMAドライバの初期化と制御
- LCD表示の更新（500ms周期）
- I2C通信のマスタとしての制御
- システム全体の起動シーケンス
```

```{swreq} Core1の責務
:id: SWR_019
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_004
:rationale: 計算系処理（統計、トレンド判定）はハードウェア非依存であり、I/O系から独立して実行できる。Core1に分離することで、将来計算量が増えてもサンプリング系に影響を与えない。

Core1は以下の責務を持つこと:
- リングバッファからのサンプル読み出し
- 統計計算（最新値、最大、最小、平均）
- トレンド判定
- 計算結果のCore0への通知
```

```{swreq} Core1起動の機構
:id: SWR_020
:status: draft
:type_kind: Functional
:layer: hal
:refines: SYS_004
:rationale: Core1起動はSIOレジスタ経由のブートシーケンスを伴うため、HAL層で機構として抽象化する。Application層はこの機構を使ってCore1のエントリ関数とスタックを指定する。

SIO HALはCore1を起動するための関数を提供すること。
関数はCore1のエントリ関数ポインタとスタックポインタを引数として受け取り、RP2040のCore1ブートシーケンスを実行すること。
```

```{swreq} Core1起動のアプリケーション層ロジック
:id: SWR_021
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_004
:rationale: Core1のエントリ関数定義、スタック確保、起動タイミングの制御はアプリケーション固有のロジック。HAL層が提供する機構を使ってアプリケーション層が起動を制御する。

アプリケーション層はCore1のエントリ関数とスタック領域を定義し、
Core0の起動シーケンスの適切なタイミングでSIO HALを呼び出してCore1を起動すること。
Core1の起動は、サンプリング機構（ADC、DMA、タイマー）の初期化完了後に行うこと。
```

```{swreq} コア間通信機構の提供
:id: SWR_022
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_004
:tbd_items: TBD-014 具体的な通信機構（FIFO、Spinlock、共有メモリ等の選択）は SYS_005 のSWR設計時に確定する。

SIO HALはコア間でデータを受け渡すための機構を提供すること。
具体的な機構の選択は、コア間データ整合性の要件（SYS_005）を満たすことを前提として決定する。
```

```{swreq} コア間通信のService層API
:id: SWR_023
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_004
:tbd_items: TBD-015 APIの具体的な形（同期送信、非同期送信、ポーリング、コールバック等）は SYS_005 のSWR設計時に確定する。

Service層はSIO HALを使ってコア間でデータを受け渡すAPIを提供すること。
アプリケーション層はこのAPIを通してコア間通信を行い、HAL層を直接呼ばないこと（レイヤ違反の回避）。
```

```{swreq} 各コアのメインループ構造
:id: SWR_024
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_004
:rationale: busy-wait方式は常にCPUを消費し、消費電力面でも他処理との並行実行面でも不利になる。ハードウェアイベントとWFI命令を組み合わせたイベント駆動構造により、CPUがアイドル時にスリープでき、各イベント処理のフローも分離されて見通しが良くなる。

Core0およびCore1のメインループはイベント駆動構造とすること。
イベントを待つ際はWFI(Wait For Interrupt)等の省電力命令によってCPUをアイドル状態に遷移させ、busy-waitによる無駄なCPU消費を行わないこと。
イベントの種類はタイマー割込、DMA完了割込、コア間通信等とする。
```

## SYS_005（コア間データ整合性）からの派生

```{swreq} 整合性が必要なデータの範囲
:id: SWR_025
:status: draft
:type_kind: Safety
:layer: service
:refines: SYS_005
:rationale: コア間で共有されるデータには性質の異なる2種類が存在する。リングバッファ（Core0→Core1、サンプル列）は最大1サンプルの不整合を許容する設計（SWR_008参照）。本要件以下で「コア間データ整合性」が対象とするのは、Core1→Core0方向の計算結果（統計値・トレンド結果）である。詳細はADR-0002参照。

本要件群は計算結果（統計値・トレンド結果）のCore1からCore0への受け渡しに関する整合性を対象とする。
リングバッファのCore0からCore1への読み出しはSWR_008の規定に従う。
```

```{swreq} 計算結果の構造体原子性
:id: SWR_026
:status: draft
:type_kind: Safety
:layer: service
:refines: SYS_005
:rationale: 統計結果（最新値・最大・最小・平均・トレンド）を構成するフィールドは互いに関連している（例: min ≤ average ≤ max）。一部のフィールドだけ更新された中間状態が読み出されると、表示が論理的に矛盾する状態になる。これを防ぐため、構造体全体を不可分に受け渡す。

Core1からCore0へ受け渡す計算結果は、構造体全体として原子的に受け渡されること。
読み手が構造体の一部のフィールドだけが新しく、残りが古い、という中間状態を読み出さないことを保証すること。
```

```{swreq} SIO FIFOによる構造体送信
:id: SWR_027
:status: draft
:type_kind: Functional
:layer: hal
:refines: SYS_005
:rationale: SIO FIFOはハードウェアが原子性を保証するメッセージパッキング機構であり、ソフトウェアによるロック実装の不具合リスクを回避できる。500ms周期・20バイト程度のデータ量では、複数ワード送信のオーバーヘッドも問題にならない。詳細はADR-0002参照。

SIO HALはSIO FIFOを用いてコア間でデータを送受信する関数を提供すること。
具体的には：
- 32bitワード単位の送信関数
- 32bitワード単位の受信関数（ブロッキングおよびノンブロッキング）
- FIFO状態の取得関数（満杯/空チェック）
```

```{swreq} 計算結果送信のService層API
:id: SWR_028
:status: draft
:type_kind: Functional
:layer: service
:refines: SYS_005
:rationale: 構造体を送る側と受ける側で、フィールドの順序や個数を独立に変更されると不整合が発生する。Service層が「構造体送受信」を抽象化することで、両端での変更の整合性を保つ。

Service層はSIO HALを使って、計算結果の構造体を送受信するAPIを提供すること。
送信側は構造体を引数として受け取り、内部で複数のSIO FIFOワード送信に分解する。受信側は逆に、複数のワード受信を組み立てて構造体として返す。
```

```{swreq} 受信側のメッセージ完全性保証
:id: SWR_029
:status: draft
:type_kind: Safety
:layer: service
:refines: SYS_005
:rationale: 構造体送信が複数ワードに分解される以上、途中で受信が中断されると壊れた構造体を読むリスクがある。受信API側でワード境界の管理を行い、構造体として完全に揃った時点でのみ呼び出し元に返す。

受信側のService層APIは、構造体を構成する全ワードを受信し終えるまで、呼び出し元に部分的な結果を返さないこと。
途中までの受信状態は内部で管理し、構造体として完全に揃った時点でのみ呼び出し元に渡すこと。
```

```{swreq} FIFO満杯時の送信側の挙動
:id: SWR_030
:status: draft
:type_kind: Safety
:layer: service
:refines: SYS_005
:tbd_items: TBD-016 FIFO満杯時の挙動（待機/古いデータ廃棄/警告）は実装段階で議論し、最適な選択を決定する。

Core1からの送信時にSIO FIFOが満杯となるケースに備え、Service層はFIFO状態を確認してから送信すること。
満杯時の挙動の選択は実装段階で確定する。
```

## SYS_006（I2C通信障害の検出と通知）からの派生

```{swreq} I2C送信失敗の検出
:id: SWR_031
:status: draft
:type_kind: Functional
:layer: hal
:refines: SYS_006
:rationale: 同期的なAPIで戻り値によりエラーを返すことで、Driver層がエラーハンドリングを直接行える。HALはステートレスを維持し、状態管理はDriver層の責務とする(ARC_002準拠)。

I2C HALの送信関数は、送信成功時に成功を示す値、送信失敗時に失敗を示す値（エラーコード）を戻り値として返すこと。
失敗の主な原因はNACK（スレーブ未応答）とタイムアウトとする。
HAL層は失敗回数等の状態を保持しないこと。
```

```{swreq} エラー状態への遷移
:id: SWR_033
:status: draft
:type_kind: Safety
:layer: driver
:refines: SYS_006
:tbd_items: TBD-007 連続失敗の閾値5回は仮置き、実機で誤検出と検出感度のバランスを観察して調整する。

連続失敗カウンタが5回に達した時、LCD Driverエラー状態へ遷移し、表示要求に対して即座に失敗を返すモードに入ること。
ただしバックグラウンドではI2C送信を試行し続け、回復検出を行うこと。
```

```{swreq} エラー状態の上位層への通知
:id: SWR_034
:status: draft
:type_kind: Functional
:layer: driver
:refines: SYS_006
:rationale: 戻り値による同期的な通知パターンに統一する（ADR-0003候補）。Application層が表示要求の都度、戻り値を見て対応する。

LCD Driverの表示関数は、エラー状態または送信失敗時に、失敗を示す戻り値を返すこと。
Application層はこの戻り値を見てLED通知の開始判断を行うこと。
```

```{swreq} 回復検出と自動再初期化
:id: SWR_035
:status: draft
:type_kind: Functional
:layer: driver
:refines: SYS_006
:rationale: LCDの電源断などからの復帰時にはHD44780の初期化シーケンスを再実行する必要がある。この回復処理はLCDの内部状態管理であり、Driver層の責務(ARC_003準拠)。Application層に再初期化の知識を持たせない。

LCD Driverはエラー状態にある間も、表示要求が来たタイミング（または独自のリトライタイミング）でI2C送信を試行すること。
送信が成功したときは、LCDが電源断などから復帰した可能性があるとして再初期化シーケンスを自動的に実行し、その後通常状態へ復帰すること。
```

```{swreq} 再初期化中のビジー応答
:id: SWR_036
:status: draft
:type_kind: Safety
:layer: driver
:refines: SYS_006
:rationale: 再初期化シーケンスは数ms程度を要する。500ms周期の表示要求とは時間スケールが大きく異なるため、再初期化中は次の表示要求を受け付けないことで状態遷移をシンプルに保つ。Application層は次の500ms周期で再試行できる。

LCD Driverが再初期化シーケンスの実行中にApplication層から新たな表示要求を受けた場合、ビジー状態を示す戻り値を返して要求を受け付けないこと。
Application層は次の周期で再試行することを想定する。
```

```{swreq} GPIO HALの提供
:id: SWR_037
:status: draft
:type_kind: Functional
:layer: hal
:refines: SYS_006
:rationale: 汎用的なGPIO抽象化として実装することで、LED以外の用途（デバッグピン、テストポイント等）にも流用可能。HALはステートレスで、ピン操作の薄いラッパに留める(ARC_002準拠)。

GPIO HALはRP2040の任意のGPIOピンに対する以下の操作を提供すること：
- ピンを出力モードに設定
- ピンをHigh/Lowに設定
- 入力モードでの値の読み取り（将来用、本要件群では未使用）
GPIO HALは状態を保持しないこと。
```

```{swreq} LED Driverによる点滅パターン管理
:id: SWR_038
:status: draft
:type_kind: Functional
:layer: driver
:refines: SYS_006
:tbd_items: TBD-008 点滅パターン（周期、デューティー比）はLEDの視認性を実機で確認後に決定。エラーの種類別に異なるパターンを使う設計も将来的に検討する。

LED Driverはオンボードのオン/オフを制御する点滅パターンを管理すること。
点滅の有効化・無効化と、パターンに応じたGPIO出力の更新を担うこと。
PicoのオンボードLEDがGPIO25に接続されている前提とするが、ピン番号はLED Driverの内部定数とし、GPIO HALには汎用ピン番号を渡すこと。
```

```{swreq} Application層によるLED制御の判断
:id: SWR_039
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_006

Application層はLCD Driverの戻り値を監視し、エラー検出後にLED Driverへ点滅開始を指示すること。
連続成功検出時には点滅停止を指示すること。
連続成功の判定基準は次のSWRで定義する。
```

```{swreq} LED通知停止の判定基準
:id: SWR_040
:status: draft
:type_kind: Functional
:layer: application
:refines: SYS_006
:rationale: 単発の成功直後にエラー通知を停止すると、表示が一瞬出てまた消える、LEDが点滅と消灯を繰り返すといったチャタリング的な挙動になる。連続成功の確認により安定して回復したことを判定する。

エラー通知中（LED点滅中）の状態で表示が成功したとき、即座にLED通知を停止せず、連続成功が一定回数続いたタイミングで停止指示を出すこと。
連続成功の閾値は3回とする。
```
