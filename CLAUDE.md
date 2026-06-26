# CLAUDE.md

このファイルは Claude Code (claude.ai/code) がこのリポジトリを扱う際に参照するプロジェクト固有の指示書である。
プロジェクトの土台となる方針を記述し、詳細な観点や手順は `.claude/` 配下に分割している。

## プロジェクト概要

RP2040 の内蔵温度センサを使った学習用ファームウェアプロジェクト。

### 目的

- ベアメタル開発の理解(Pico SDK を使わず、SVD からヘッダ生成、リンカスクリプト、boot2、crt0 を自作)
- ASPICE V字モデルに準拠した開発プロセスの実践
- GitHub Flow を用いたチーム開発作法の練習
- C 言語での実装後、Rust への移植を行い、両者を比較

### ハードウェア前提

- **MCU**: Raspberry Pi Pico (RP2040、ARM Cortex-M0+ デュアルコア)
- **温度センサ**: RP2040 内蔵温度センサ (ADC4)
- **表示**: I2C 接続の LCD1602
- **状態表示**: オンボード LED (GPIO 25)

### 開発環境

- **ホスト**: Mac mini (Apple Silicon / aarch64)
- **コンテナ**: VSCode Dev Containers
  - docs コンテナ: Sphinx + sphinx-needs + PlantUML(ドキュメントビルド用)
  - firmware-c コンテナ: Ubuntu 24.04 + Clang 18 + Arm GNU Toolchain 14.2(C 実装用)
- **デバッガ**: gdb-multiarch + OpenOCD
- **書き込み**: USB マスストレージモード (UF2)

## プロジェクトの方向性

本プロジェクトは学習目的だが、以下の長期的な方向性を意識して設計する。
Claude Code はレビュー時、目の前のコード/ドキュメントだけでなく、
これらの方向性に沿っているかも確認する。

### 言語の段階的移行: C → Rust

**最終目標**: 全実装を Rust 化する。

**移行ステップ**:

1. 段階3〜4: C 言語で全機能を実装、テストまで完了
2. 段階5〜9: Rust 移植
   - 初期段階では FFI を使い、C と Rust を混在させて段階的に移植する
   - FFI の境界設計、ABI 互換性、メモリ安全性の境界条件を学ぶ
   - 最終的に全てを Rust に置き換え、FFI を削除
3. 段階10: 両言語の比較ドキュメント作成

### ハードウェアの抽象化: RP2040 → RP2350 など

**直近の対象**: RP2040(Raspberry Pi Pico)

**将来の意識**: RP2350(Raspberry Pi Pico 2)など、後継・派生チップへの移植可能性を保つ。

HAL 層の設計を行う際は、特定チップへの密結合を避けるよう意識する。
ただし、過度な抽象化はしない。学習プロジェクトとして、まずは RP2040 で動くことを優先する。

## ASPICE プロセス対応

本プロジェクトは ASPICE V字モデルに準拠する。

| プロセス | 内容 | 対応ファイル |
|---|---|---|
| SYS.2 | システム要件分析 | `docs/common/10_system_requirements.md` |
| SYS.3 | システムアーキテクチャ設計 | **省略**(ハードウェア構成は前提、`00_overview.md` に記載) |
| SWE.1 | ソフトウェア要件分析 | `docs/common/20_software_requirements.md` |
| SWE.2.1 | ソフトウェアアーキテクチャ設計 | `docs/common/30_architecture.md` |
| SWE.2.2 | コンポーネント設計 | `docs/common/40_component_design.md`(段階2.5-2で作成予定) |
| SWE.3.1 | 詳細設計 | `docs/common/50_detailed_design.md`(Doxygen 補完、段階2.5-3で作成予定) |
| SWE.3.2 | 実装 | `firmware-c/src/` 配下 |
| SWE.4 | ユニットテスト | 段階4-1 |
| SWE.5.2 | コンポーネントテスト | 段階4-2 |
| SWE.5.1 | 統合テスト | 段階4-3 |
| SWE.6 | 受け入れテスト | 段階4-4 |

### V字モデルの設計とテストのペア

各設計段階で対応するテストも設計する:

- SWE.2.1 (アーキテクチャ設計) → 統合テスト設計
- SWE.2.2 (コンポーネント設計) → コンポーネントテスト設計
- SWE.3.1 (詳細設計) → ユニットテスト設計

## 段階構成

```
段階1: 要件分析(完了)
段階2: ベアメタル基盤(チュートリアル位置づけ、進行中)
  段階2-A: dev container 構築(完了)
  段階2-B: SVD → C ヘッダ生成(完了)
  段階2-C: リンカスクリプト、boot2、crt0
    段階2-C-1: 座学 + Doxygen 導入(完了)
    段階2-C-2: boot2 取り込みと日本語コメント(完了)
    段階2-C-3: リンカスクリプト
    段階2-C-4: crt0
    段階2-C-5: 動作確認用最小プログラム
  段階2-D: 実機動作確認とデバッグ・観測環境の確立
    段階2-D-1: OpenOCD/gdb 接続確立（ブレーク・レジスタ / メモリ確立）
    段階2-D-2: LED 点滅（crt0 + 最小main、観測はgdbとLED）
    段階2-D-3: クロック初期化（XOSC / PLL / clk_peri） + UARTログ確立
段階2.5: 設計フェーズ(ASPICE V字モデル準拠)
  段階2.5-1: アーキテクチャ設計 + 統合テスト設計
  段階2.5-2: コンポーネント設計 + コンポーネントテスト設計
  段階2.5-3: 詳細設計 + ユニットテスト設計
段階3: 実装フェーズ(SWE.3.2)
  段階3-1: HAL 層
  段階3-2: Driver 層
  段階3-3: Service 層
  段階3-4: Application 層
段階4: テスト実施フェーズ
  段階4-1: ユニットテスト実施
  段階4-2: コンポーネントテスト実施
  段階4-3: 統合テスト実施
  段階4-4: 受け入れテスト実施
段階5〜9: Rust 移植
段階10: 言語比較ドキュメント
```

## ディレクトリ構成

```
rp2040-temp-monitor/
├── CLAUDE.md                  ← このファイル
├── .claude/                   ← Claude Code 用の専門指示書
│   ├── review/                ← レビュー専門ファイル
│   │   ├── principles.md
│   │   ├── doc_review.md
│   │   └── typo_check.md
│   └── commands/              ← スラッシュコマンド(将来用)
├── CONTRIBUTING.md            ← 開発の進め方
├── README.md                  ← プロジェクト概要、進捗ステータス
├── Makefile                   ← docs ビルド用
├── .github/
│   ├── workflows/             ← GitHub Actions
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── docs/                      ← Sphinx + sphinx-needs ドキュメント
│   ├── conf.py
│   ├── index.md
│   └── common/                ← ASPICE プロセス順
│       ├── 00_overview.md
│       ├── 10_system_requirements.md
│       ├── 20_software_requirements.md
│       ├── 30_architecture.md
│       ├── 99_traceability.md
│       └── adr/               ← Architecture Decision Records
├── diagrams/                  ← PlantUML 図
│   └── architecture/
└── firmware-c/                ← C 実装(段階2 以降)
    ├── .devcontainer/
    ├── Doxyfile
    ├── Makefile
    ├── svd/                   ← RP2040.svd
    ├── include/
    │   └── generated/         ← svdconv 生成ヘッダ
    ├── src/
    │   └── boot/              ← boot2、crt0(予定)
    ├── tools/                 ← ビルドスクリプト
    └── docs/                  ← Doxygen 生成(.gitignore で除外)
```

## コーディング規約(主要点)

### C コード

- 言語: C(現状は C11 を想定、後で確定)
- コンパイラ: Clang 18(ホスト/ターゲット両方)
- ターゲット: ARM Cortex-M0+(Thumb 命令)
- フォーマット: clang-format(設定ファイルは段階3 で導入予定)
- インデント: スペース 4
- 命名規則:
  - 関数: `snake_case`(例: `temp_sensor_read`)
  - 構造体: `snake_case_t` または `CamelCase`(段階3 で確定)
  - マクロ/定数: `UPPER_SNAKE_CASE`
  - レジスタ定義: SVD 生成のままを使用

### アセンブリコード

- ARM Thumb 命令(Cortex-M0+ なので Thumb 限定)
- 拡張子: `.S`(プリプロセッサ通し)
- コメント: 既存の英語コメントは残す、日本語コメントを追加
- 著作権表示は維持(BSD-3-Clause 等)

### コメント方針

- **言語**: 日本語(原文の英語コメントが既にある場合は残す)
- **形式**: Doxygen 形式(`/** ... */`)
- 関数の前には `@brief`、`@param`、`@return`、`@note`、`@see` を必要に応じて記載
- ファイル冒頭には Doxygen ファイルヘッダ(`@file`、`@brief`、`@details`、`@copyright` 等)を付ける

### Doxygen group の活用

レイヤ・コンポーネント別に `@defgroup` / `@ingroup` を使い、ドキュメントを論理的に整理する。
group の階層は本プロジェクトのアーキテクチャに対応させる。
具体的な階層は段階3 でコードを書く時に決める。

### Doxygen のその他活用機能

`@mainpage`、`@warning`、`@note`、`@attention`、`@todo`、`@bug`、`@par`、`@startuml`、`@ref` を積極的に使う。

## ドキュメント規約(主要点)

### Markdown

- 記法: MyST(Sphinx 拡張、Markdown + ディレクティブ)
- ファイル名: ASPICE プロセス順の 10刻みの番号体系
- 日本語の文章は「である調」(現状の他文書に合わせる)

### sphinx-needs

要件管理に `sphinx-needs` を使用。形式は既存ドキュメントを参照。

### PlantUML

- 配置: `diagrams/<カテゴリ>/<名前>.puml`
- 参照: Markdown 内で `{uml}` ディレクティブ
- 構文: シンプルな書き方を優先(複雑なネストは避ける)

### Doxygen

- アセンブリ: `EXTENSION_MAPPING = S=C` を設定済み
- 出力: `firmware-c/docs/api/`(`.gitignore` で除外)
- ビルド: `firmware-c/Makefile` の `make docs`

## Git / GitHub Flow

### ブランチ運用

- `master`: 常に動作する状態を保つ
- 機能ブランチ: `feature/<issue番号>-<簡潔な内容>`
- 例: `feature/5-aspice-doc-restructure`

### issue 系統

- **機能実装系**: `[段階番号]` プレフィックス(例: `[2-C-3]`)
- **開発基盤**: `[INFRA-N]` プレフィックス
- **ドキュメント整理**: `[DOC-N]` プレフィックス
- **バグ報告**: `[BUG]` プレフィックス

### コミットメッセージ

- 1行目: 簡潔な要約(50文字程度)
- 末尾に `(#<issue番号>)` を含める
- 日本語で書いてよい

### Pull Request

- タイトル: `[#<issue番号>] 簡潔な内容`
- 本文: `.github/pull_request_template.md` に従う
- マージ方法: **Squash and merge**
- マージ後はブランチを削除

### 例外

- typo 修正など軽微な変更は `master` への直接コミットを許容

## レビューの基本方針

詳細は @.claude/review/principles.md を参照。

### 基本原則(要約)

**Claude Code はレビュアーであり、コードの修正は行わない。** 問題点を指摘し、ユーザーに修正を指示する。
これは学習プロジェクトとしての方針であり、ユーザー自身が手を動かすことで理解を深めることを目的とする。

### レビュー専門ファイルの自動参照

ユーザーの作業内容に応じて、以下のファイルを Claude Code が自動的に参照する:

- **共通の基本姿勢**: @.claude/review/principles.md (全レビューで参照)
- **ドキュメントのレビュー**: @.claude/review/doc_review.md
- **typo チェック**: @.claude/review/typo_check.md

これら以外のレビュー観点(コードレビュー、テストレビュー、ASPICE 整合性レビュー、移植性レビューなど)は、
プロジェクトの段階が進むにつれて `.claude/review/` 配下に追加していく予定。

## Claude Code の使い方

### 起動

プロジェクトルートで `claude` コマンドを実行する。
CLAUDE.md と `.claude/review/principles.md` は起動時に自動的に読み込まれる。
他のレビューファイル(`doc_review.md`、`typo_check.md` など)は、
Claude Code が文脈から判断して必要時に参照する。

### レビュー依頼の例

#### ドキュメントレビュー

```
> docs/common/30_architecture.md をレビューしてください
```

→ Claude Code が `.md` ファイルと判断し、`.claude/review/doc_review.md` を参照してレビュー。

#### typo チェック

```
> docs/ 配下のファイル全体で typo をチェックしてください
```

→ Claude Code が `.claude/review/typo_check.md` を参照して、プロジェクト固有の単語リストや
表記揺れパターンに従ってチェック。

#### PR レビュー

```
> 現在のブランチの変更を master との差分でレビューしてください
```

→ Claude Code が `git diff master..HEAD` で差分を確認し、変更内容に応じた観点で総合レビュー。

#### 複数観点での同時レビュー

```
> このPRをドキュメント観点と typo の両方でレビューしてください
```

→ 両方のレビューファイルを参照してレビュー。

### 指示のコツ

#### 対象を明確に

良い: 「`docs/common/30_architecture.md` をレビューしてください」
避けたい: 「レビューお願いします」(何をレビューするか曖昧)

#### 観点を明示

良い: 「ドキュメント観点でレビューしてください」「typo を集中的にチェックしてください」
避けたい: 「見てください」(何の観点か不明)

#### 重要度の指定

レビュー結果は `principles.md` の重要度区分(必須/推奨/提案)に従う。
特定の重要度に絞って依頼することもできる。

```
> 重要度「必須」のみで、本当に直すべき点だけ教えてください
```

```
> 提案レベルでも構わないので、改善点を全部教えてください
```

#### 出力フォーマットの指定

```
> 結果を Markdown 形式で、ファイル別にまとめてください
```

```
> 修正案のコードブロックも含めて出力してください
```

### スラッシュコマンドについて

現時点ではスラッシュコマンドは導入していない(`.claude/commands/` は空)。
自然な文章での指示で十分対応できるため。

定型作業が増えてきた、または特定の依頼パターンを繰り返したい場合に、
将来 `.claude/commands/` 配下にコマンドを追加することがある。

## 作業時間の記録（打刻運用）

各 issue の作業時間を計測するため、作業の開始・終了時に打刻する。

- 作業開始時: `/start-work <issue番号>` を実行する（issueコメントに `WORK_START` が記録される）
- 作業終了時: `/end-work <issue番号>` を実行する（`WORK_END` と作業内容の要約が記録される）
- 打刻データは `script/collect_worklog.py` が集計し、CI が GitHub Pages の「進捗・工数レポート」に反映する
- 1作業者・1 issue 内で `WORK_START` が連続したり `WORK_END` が対応する開始を持たない場合、レポートの「打刻の不整合」に警告として表示される

### Claude Code への依頼

- 作業を開始する際、打刻がまだであれば `/start-work` の実行を促すこと
- 作業を終了・コミットする際、`/end-work` での打刻を促すこと
- 打刻そのものの代行はせず、開発者に実行を促す（打刻は本人の作業記録であるため）

## してはいけないこと

- **マージは自動でしない**(人間が必ず確認)
- **大きな設計判断は ADR なしで進めない**
- **typo 修正以外で `master` への直接コミットをしない**
- **`feature/*` 以外のブランチ命名は避ける**
- **既存の英語コメント(参考実装からの取り込み)を削除しない**
- **著作権表示を削除/改変しない**(BSD-3-Clause 等)
- **ハードウェア依存の値(レジスタアドレス等)をマジックナンバーで書かない**(SVD 生成ヘッダ経由で参照する)
- **コミットメッセージから issue 番号を省略しない**

## CLAUDE.md の拡張方針

CLAUDE.md が肥大化するのを防ぐため、以下の原則で内容を分割する。

### このファイル(CLAUDE.md)に書く内容

- プロジェクト全体の方針(土台、変わりにくい)
- 全てのレビューで共通する基本姿勢の要約
- ディレクトリ構造、規約の概要
- Git/GitHub Flow

### `.claude/review/` に書く内容

- タスク別の詳細指示(レビューの観点、チェック手順)
- 専門領域(ドキュメント、テスト、コード、ASPICE、移植性、typo など)の深い知識

### `.claude/commands/` に書く内容

- スラッシュコマンドの定義(将来用)

### 追加方針

- 必要が生じた時に追加する(最初から全部作らない)
- 各ファイルは「ロール」を持つ(例: ドキュメントレビュー専門)
- ユーザーが明示的に指定しなくても、Claude Code は文脈から適切なファイルを自動参照する
- 必要に応じてユーザーがスラッシュコマンドで明示呼び出しもできる(将来)

## 参考リンク

- リポジトリ: <https://github.com/harukikiya/rp2040-temp-monitor>
- 公開ドキュメント: <https://harukikiya.github.io/rp2040-temp-monitor/>
- RP2040 datasheet: <https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf>
- ASPICE: <https://en.wikipedia.org/wiki/Automotive_SPICE>

## このファイルの更新

このファイルはプロジェクトの方針が変わった時に更新する。
更新時は `[INFRA-N]` または `[DOC-N]` の issue を立てて PR で変更する。