# typo チェック

このファイルは typo(誤字脱字、スペルミス)をチェックする際の観点と手順を記述する。

レビューの基本姿勢は `.claude/review/principles.md` を参照。

## 観点

### 1. 英単語のスペルミス

よくあるパターン:

- 二重子音の抜け落ち(例: `comitted` → `committed`)
- 母音の入れ替わり(例: `Temparature` → `Temperature`)
- 文字の入れ替わり(例: `Satege` → `Stage`、`archtecture` → `architecture`)
- 余分な/不足する文字(例: `recieve` → `receive`)

### 2. プロジェクト固有の単語

正しい表記を確認:

- `RP2040`(R と P の間にハイフンなし、`R-2040` ではない)
- `RP2350`(同上)
- `Cortex-M0+`(`Cortex M0+` ではない、ハイフンあり)
- `Raspberry Pi Pico`(`Raspberrypi`、`Pi Pico` などにしない)
- `QSPI`(`Q-SPI`、`Qspi` ではない)
- `boot2`(`Boot2`、`BOOT2` も避ける、原則として小文字)
- `ASPICE`(`Aspice` ではない)
- `Doxygen`(`doxygen` は文中では避ける、固有名詞として大文字始まり)
- `Sphinx`(`sphinx` は固有名詞として大文字始まり)
- `sphinx-needs`(これは小文字、ハイフン区切りで一語)
- `PlantUML`(`Plantuml`、`Plant UML` ではない)
- `GitHub`(`Github`、`github` ではない、表記揺れ注意)

### 3. ASPICE 用語

正しい表記を確認:

- `SYS.2`、`SYS.3`(ドットあり、`SYS2`、`SYS-2` ではない)
- `SWE.1`、`SWE.2.1`、`SWE.2.2`、`SWE.3.1`、`SWE.3.2`、`SWE.4`、`SWE.5.1`、`SWE.5.2`、`SWE.6`
- `V字モデル`(`V字型モデル`、`V型モデル` ではない、本プロジェクトの統一表記)

### 4. 略語の表記

- `ADC`(Analog-to-Digital Converter)
- `DMA`(Direct Memory Access)
- `I2C`(`I²C` の表記もあるが、本プロジェクトでは `I2C` で統一)
- `SPI`(Serial Peripheral Interface)
- `UART`(Universal Asynchronous Receiver-Transmitter)
- `GPIO`(General Purpose Input/Output)
- `SVD`(System View Description)
- `XIP`(eXecute In Place)
- `SSI`(Synchronous Serial Interface)
- `FFI`(Foreign Function Interface)

### 5. 数値・単位の表記

- 周波数: `133MHz`、`12MHz` のような表記(`133 MHz` の半角スペースありも許容、統一すること)
- 容量: `256KB`、`2MB`(`256 KB` のスペースあり/なし、統一すること)
- 時間: `500ms`、`10s`(`500 ms` のスペースあり/なし、統一すること)
- ピン番号: `GPIO 25`、`GPIO25`(統一すること)

### 6. 日本語の表記揺れ

- 「ファームウェア」(`ファームウエア` は避ける)
- 「コンピューター」と「コンピュータ」(プロジェクト内で統一)
- 「アーキテクチャ」(`アーキテクチャー` は避ける)
- 「インタフェース」と「インターフェース」(プロジェクト内で統一)
- 「メモリ」と「メモリー」(プロジェクト内で統一)
- 数字の半角/全角(本プロジェクトでは半角で統一)

### 7. ファイル名・パスの表記

- ファイル名はバッククォート(`` ` ``)で囲む(例: `` `boot2_w25q080.S` ``)
- パスもバッククォートで囲む(例: `` `firmware-c/src/boot/` ``)
- コードブロックの中ではバッククォート不要

### 8. コードブロックの言語指定

- C コードは `` ```c ``
- Bash は `` ```bash ``
- YAML は `` ```yaml ``
- Python は `` ```python ``
- Markdown は `` ```markdown ``
- 言語が分からない場合は `` ``` `` のみで可(言語指定なし)

## 手順

### ファイル全体のチェック

1. 対象ファイルを読み込む
2. 観点1〜8 を適用しながら一行ずつチェック
3. 疑わしい箇所は周辺の文脈と合わせて判断

### 特定パターンの集中チェック

ユーザーから「プロジェクト名の表記を全部チェックして」のような依頼があった場合:

1. プロジェクトで頻出する固有名詞・略語を grep などで確認
2. 表記揺れがないか網羅的にチェック
3. 結果を一覧で報告

## 出力フォーマット

```
[必須] ファイル名:行番号
  検出: <誤った表記>
  修正: <正しい表記>
  理由: <なぜ修正が必要か(規約、表記揺れの統一など)>
```

例:

```
[必須] docs/index.md:1
  検出: R2040 Temparature Monitor
  修正: RP2040 Temperature Monitor
  理由: 製品名は「RP2040」(P を含む)、「Temperature」(e ではなく a が誤り)。
        正しい英語表記とプロジェクト固有の表記の両方の規約に該当。

[推奨] docs/common/30_architecture.md:45
  検出: アーキテクチャー
  修正: アーキテクチャ
  理由: プロジェクトでは「アーキテクチャ」で統一(他文書での表記と合わせる)。
```

## このファイルの更新方針

新しい表記揺れパターンが見つかった時、本ファイルに追記する。
プロジェクト固有の単語や略語が増えた時(段階3 で新しいライブラリを導入する時など)、
本ファイルにエントリを追加する。

更新は `[INFRA-N]` issue でPR として行う。