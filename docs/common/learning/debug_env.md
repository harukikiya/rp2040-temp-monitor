---
type: learning
title: デバッグ環境（OpenOCD + gdb）
description: debugprobe 経由で RP2040 に接続し、halt・レジスタ・メモリを操作する手順
tags: [debug, openocd, gdb]
stage: "2-D"
---

# デバッグ環境（OpenOCD + gdb）

段階 2-D-1 で確立した、実機の観測手段をまとめる。ファームウェアを書き込む前でも
bootrom 相手に接続できるため、以降の段階（LED 点滅・クロック初期化）で
「動かないときに中を覗く」唯一の手段になる。

## 構成：なぜホストとコンテナで分業するのか

macOS の Docker は USB デバイスをコンテナに渡せない。firmware-c コンテナには
openocd も gdb-multiarch も入っているが、コンテナ内の OpenOCD からは debugprobe が見えない。
そこで次のように分ける。

- **OpenOCD**：macOS ホストで実行（USB で debugprobe と通信する側）
- **gdb-multiarch**：firmware-c コンテナで実行（ビルド成果物 .elf を読む側）
- 両者は **TCP** で接続する（コンテナ → ホスト）

``` text
[RP2040] --SWD--> [debugprobe] --USB--> [macOS: OpenOCD] <--TCP--> [コンテナ: gdb]
                                          :3333 = core0
                                          :3334 = core1
```

## 接続手順

### 0. 配線

Debug Probe 本体には 3 ピンのコネクタが 2 つある。**`D`（Debug = SWD）を使う**。
`U`（UART）に挿すと、プローブ自体は USB で正常に認識されるのに
ターゲットとだけ通信できない、という紛らわしい失敗になる（実際に踏んだ）。

`D` コネクタは電源を供給しないため、**ターゲットの Pico は別途 USB で給電**する。

### 1. ホストで OpenOCD を起動

``` bash
openocd -f interface/cmsis-dap.cfg -c "adapter speed 5000" \
        -f target/rp2040.cfg -c "bindto 0.0.0.0"
```

- `bindto 0.0.0.0` は必須。既定では localhost にのみ束縛され、コンテナから届かない。
- `adapter speed 5000`（5 MHz）を指定する。省略すると 100kHz で動作し、
  フラッシュプローブ中に `keep_alive() was not invoked in the 1000 ms timelimit`
  警告が出る（実害はないが遅い）。
- 現在の debugprobe は CMSIS-DAP 互換のため `interface/cmsis-dap.cfg` を使う
  （旧 picoprobe.cfg や Raspberry Pi フォーク版 OpenOCD のビルドは不要）。

成功すると次のログが出る（要点のみ）。

``` text
Info : Using CMSIS-DAPv2 interface with VID:PID=0x2e8a:0x000c
Info : SWD DPIDR 0x0bc12477, DLPIDR 0x00000001
Info : [rp2040.core0] Cortex-M0+ r0r1 processor detected
Info : [rp2040.core1] Cortex-M0+ r0r1 processor detected
Info : Listening on port 3333 for gdb connections
Info : Listening on port 3334 for gdb connections
```

`DPIDR` が読めていればターゲットとの SWD 通信は成功している。
`Listening on port 3333` が出ない場合、ターゲット初期化に失敗している。

### 2. コンテナの gdb から接続

OpenOCD は起動したままにして、別のターミナルでコンテナに入る。

``` bash
gdb-multiarch
```

``` text
(gdb) target extended-remote host.docker.internal:3333
```

接続すると自動的に halt する（`monitor halt` が無反応に見えるのはこのため）。
`.elf` を読み込む場合は `file build/firmware.elf` を先に実行する（2-D-2 以降）。
ファーム未書き込みの段階では bootrom 内で停止するため、
`No executable has been specified` 警告と `0x000020e0 in ?? ()` は正常。

### 3. 基本操作

``` text
(gdb) monitor halt          # コアを停止
(gdb) info registers        # レジスタ一覧
(gdb) x/4xw 0x20000000      # メモリ read（SRAM）
(gdb) set {int}0x20000000 = 0xDEADBEEF  # メモリ write
(gdb) monitor reset halt    # リセットして停止状態から開始
```

## 接続確認に使えるアドレス

ファームウェアが無くても読める既知の値。接続の成否を切り分けられる。
以下は実測値（2-D-1 時点）。

| アドレス | 内容 | 実測値 |
| --- | --- | --- |
| 0x40000000 | SYSINFO CHIP_ID | `0x20002927` |
| 0x00000000 | bootrom [0] = 初期 SP | `0x20041f00` |
| 0x00000004 | bootrom [1] = リセットベクタ | `0x000000eb` |
| 0x20000000 | SRAM 先頭 | write した値が読み返せる |

CHIP_ID の内訳：

- 下位 12 bit `0x927` = JEDEC 製造者 ID（Raspberry Pi）
- 続く 16 bit `0x0002` = パート番号（RP2040）
- 最上位 4 bit `0x2` = リビジョン（B0。OpenOCD のログにも `RP2040 B0` と出る）

リセットベクタが奇数（`0x...eb`）なのは Thumb ビットが立っているため。
crt0 のベクタテーブルで `Reset_Handler | 1` としているのと同じ理由。

全て `0x00000000` や `0xffffffff` が返る場合、接続が成立していない。

## つまずきどころ

- **`Failed to connect multidrop rp2040.dap0`**：プローブは USB で認識されている
  （`Using CMSIS-DAPv2 interface` が出ている）のに、ターゲットの DAP が応答しない状態。
  実際の原因は **Debug Probe の `U`（UART）コネクタに挿していた**ことだった。
  `D`（Debug）に挿し替えて解決。他に、ターゲット Pico の給電漏れ、
  SWCLK と SWDIO の入れ替わり、ジャンパの接触不良も同じ状態になる。
- **コンテナから接続できない**：`bindto 0.0.0.0` の付け忘れが最有力。
  `host.docker.internal` が解決できない環境ではホストの LAN IP を直接指定する。
- **`keep_alive() was not invoked...` 警告**：アダプタ速度が既定の 100 kHz のため。
  `adapter speed 5000` を指定すれば出なくなる。
- **core1 に繋いでしまう**：3333 が core0、3334 が core1。単一コアの作業では 3333 を使う。

## 副次的に分かること

OpenOCD は接続時に外部 QSPI フラッシュもプローブする。

```text
Info : Found flash device 'win w25q16jv' (ID 0x001540ef)
Info : RP2040 B0 Flash Probe: 2097152 bytes @0x10000000, in 32 sectors
```

boot2（`boot2_w25q080.S`）が前提としているフラッシュと実機が一致していることの確認になる。

## ファームウェアの書き込み

段階 2-D-2 以降で使う手順。ビルドはコンテナ、書き込みはホストで行う。

### 1. コンテナでイメージを生成

```bash
make firmware
```

`build/firmware.bin` ができる。先頭 256 バイトが boot2 で、末尾 4 バイトの CRC 欄は
`--patch` によって埋められている。CRC 欄が 0 のままだと bootrom に拒否される。

### 2. ホストから書き込み

**リポジトリのルートで実行する。** OpenOCD は相対パスをカレントディレクトリから
解決するため、ホームディレクトリのまま実行すると
`couldn't open firmware-c/build/firmware.bin` になる（実際に踏んだ）。

```bash
cd <リポジトリのルート>
openocd -f interface/cmsis-dap.cfg -c "adapter speed 5000" -f target/rp2040.cfg \
        -c "program firmware-c/build/firmware.bin verify reset exit 0x10000000"
```

`** Verified OK **` が出れば成功。`exit` を付けているので OpenOCD は終了する。

### 3. 起動の確認

書き込み直後にファームが起動する。bootrom が boot2 を受理したことは、次で確認できる。

- **LED が点滅する**（2-D-2 の場合）
- **RPI-RP2 ドライブが消える**。書き込み前は USB マスストレージとしてマウント
  されているため、macOS が「ディスクの不正な取り出し」を表示する。これは
  マスストレージが止まって自前のファームが動き出したことの裏返しである。
- 逆に **RPI-RP2 のままマウントされ続ける場合は boot2 が拒否されている**。
  CRC 欄が埋まっているか、書き込みアドレスが 0x10000000 かを確認する。

### 4. gdb で動作を確認

ホストで OpenOCD を起動したままにする（`program ... exit` ではない方）。

```bash
openocd -f interface/cmsis-dap.cfg -c "adapter speed 5000" -f target/rp2040.cfg -c "bindto 0.0.0.0"
```

コンテナで `.elf` を渡して gdb を起動すると、シンボル付きで確認できる。

```bash
gdb-multiarch build/firmware.elf
```

```text
(gdb) target extended-remote host.docker.internal:3333
(gdb) monitor halt
(gdb) info registers pc
(gdb) backtrace
```

2-D-2 時点での実測:

```text
pc             0x100002ac          0x100002ac <delay_loop+12>
#0  0x100002ac in delay_loop ()
#1  0x10000244 in main ()
```

pc がフラッシュ領域（0x1000xxxx）にあり、backtrace に `main` が現れることで、
bootrom ではなく自前ファームが動作しており、crt0 から main が呼ばれていることが
確認できる。

## クロック未初期化での時間の不正確さ

段階 2-D-2 の時点ではクロックを初期化していないため、システムクロックは ROSC
（リングオシレータ、公称約 6.5 MHz）で動作する。

遅延ループ 200,000 回で点滅周期が約 0.3 秒（半周期 0.15 秒）だったことから、
おおよそのクロック周波数を逆算できる。

- 200,000 回 ÷ 0.15 秒 ≒ 1.33 M回/秒
- 最適化なしのループは 1 回転あたりおよそ 5 命令
- 1.33 M × 5 ≒ **約 6.7 MHz** → ROSC の公称値とほぼ一致

ROSC は温度・電圧・個体差で変動するため、この値に保証はない。正確な時間制御と
UART のボーレート生成には、段階 2-D-3 で XOSC（12 MHz 水晶）と PLL による
クロック初期化が必要になる。
