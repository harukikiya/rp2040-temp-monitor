# アーキテクチャ要件

本プロジェクトのソフトウェアアーキテクチャに関する要件を記述する。
レイヤ構成、各層の責務、テスト境界などを定義する。

## レイヤ構成

```{uml} ../../diagrams/architecture/layered_architecture.puml
```

## 構成要件

```{arc} 6レイヤアーキテクチャ
:id: ARC_001
:status: draft
:type_kind: Functional
:refines: SYS_001, SYS_002, SYS_003

ソフトウェアは以下の6層から構成されること：

- Application Layer: アプリケーション固有の振る舞い
- Service Layer: ハードウェア非依存のロジック
- Driver Layer: 具体デバイスの抽象化
- HAL (Hardware Abstraction Layer): ペリフェラルの抽象化
- Register Access Layer: SVDから生成されたレジスタ定義
- Hardware: RP2040の物理ハードウェア

各層は直下の層のみに依存し、上位層への参照を持ってはならない。
```

```{arc} HAL層の責務
:id: ARC_002
:status: draft
:type_kind: Functional
:refines: ARC_001

HAL層はRP2040のペリフェラル（ADC、DMA、I2C、Timer、SIO）を
抽象化したインタフェースを提供すること。
HAL関数は副作用としてレジスタアクセスを伴うが、その他の状態管理は持たないこと（ステートレス）。
```

```{arc} Driver層の責務
:id: ARC_003
:status: draft
:type_kind: Functional
:refines: ARC_001

Driver層は具体的なデバイス（LCD1602、ADC+DMA連携など）を
抽象化したインタフェースを提供すること。
複数のHAL関数を組み合わせ、デバイス固有の初期化シーケンスや状態管理を担うこと。
```

```{arc} Service層の責務
:id: ARC_005
:status: draft
:type_kind: Safety
:refines: ARC_001

Service層の全てのモジュールは、ホストPC上（x86_64またはARM64）で
コンパイル・実行可能であり、ホスト側でユニットテストが可能であること。
これによりハードウェアなしで論理層の品質が保証されること。
```

```{arc} HAL層のモック可能性
:id: ARC_006
:status: draft
:type_kind: Safety
:refines: ARC_005

HAL層のインタフェースはモック実装の置き換え可能であること。
これによりDriver層およびService層をホスト側でユニットテストできること。
```

```{arc} 単方向依存の徹底
:id: ARC_007
:status: draft
:type_kind: Safety
:refines: ARC_001

各層からの依存は直下の層のみに許可される。
下位層から上位層へのコールバックが必要な場合は、関数ポインタの登録など、
依存方向を反転させる手法を用いること。
```

## コア間のデータフロー

本システムはCore0（I/O系）とCore1（計算系）で責務を分担する（SYS_004、SWR_018、SWR_019）。
両コアの間でどのようにデータが受け渡されるかを以下に示す。

```{uml} ../../diagrams/architecture/inter_core_data_flow.puml
```

### データフローの3段階

**第1段階：センサ → リングバッファ（Core0領域）**

ADCのサンプリング結果は、DMAによってCPU介入なしにリングバッファへ転送される。
リングバッファはCore0が管理する領域だが、Core1からも読み出し可能とする。

**第2段階：リングバッファ → 統計/トレンド結果(Core1)**

Core1は500ms周期でリングバッファからサンプル列を読み出し、統計値とトレンド結果を計算する。
読み出し中もCore0（DMA経由）による書き込みは継続しており、
最大1サンプル分の不整合を許容する設計（SWR_008）。

**第3段階：統計/トレンド結果 → LCD表示（Core0）**

Core1の計算結果は共有メモリ領域を通じてCore0へ受け渡される。
Core0はこの結果を読み出して、LCDに表示する。
具体的な受け渡し機構（SIO FIFO、Spinlock、共有バッファ等）はコア間データ整合性要件（SYS_005）に従って次回設計する。

### 重要な設計論点

このデータフローは2種類のコア間共有データが存在する：

1. **リングバッファ**：Core0が書き、Core1が読む。サンプリング系。
2. **計算結果**：Core1が書き、Core0が読む。表示系。

両者は方向もデータ量も性質も異なるため、適切な機構の選択がSYS_005のSWRで議論される予定である。
