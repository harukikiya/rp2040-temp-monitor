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
