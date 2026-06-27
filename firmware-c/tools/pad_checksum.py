#!/usr/bin/env python3
"""boot2（Boot Stage 2）に RP2040 bootrom 用の CRC32 チェックサムを付加する。

CRC とは：
    CRC（Cyclic Redundancy Check, 巡回冗長検査）は、データのビット列を 1 つの
    多項式と見做し、あらかじめ決めた生成多項式で割った「余り」を検査値とする
    誤り検出符号である。データが 1 ビットでも変化すると検査値が大きく変わるため、
    転送や保存の途中で生じた破損を高い確率で検出できる。単純なバイト総和よりも
    検出力が高い「チェックサム」の一種と考えてよい。

RP2040 のブート ROM は、フラッシュ先頭 256 バイト（boot2）のうち先頭 252 バイトに
対する CRC-32/MPEG-2 を、末尾 4 バイト（リトルエンディアン）と照合する。一致しなければ
boot2 を実行せず、USB ブートローダ（RPI-RP2 ドライブ）に落ちる。

CRC-32/MPEG-2 のパラメータ：
    poly    = 0x04C11DB7
    init    = 0xFFFFFFFF
    refin   = False         （MSB-first, 入力ビット反転なし）
    refout  = False         （出力ビット反転なし）
    xorout  = 0x00000000
    check   = 0x0376E6E7    （"123456789"）

参考：RP2040 Datasheet 2.8.1.3.1 (Checksum)
"""
from __future__ import annotations

import argparse
import struct
import sys

BOOT2_TOTAL: int = 256                      # boot2 全体サイズ（固定）
CRC_SIZE: int = 4                           # 末尾チェックサムのバイト数
PAYLOAD_SIZE: int = BOOT2_TOTAL - CRC_SIZE  # CRC 対象 = 先頭 252 バイト

POLY: int = 0x04C11DB7                       # 生成多項式
INIT: int = 0xFFFFFFFF                       # CRC レジスタの初期値
MASK: int = 0xFFFFFFFF                       # 32 ビットへの切り詰め用マスク
CHECK_VALUE: int = 0x0376E6E7                # CRC-32/MPEG-2 標準チェック値

def crc32_mpeg2(data: bytes) -> int:
    """CRC-32/MPEG-2 を計算する。
    
    MSB ファースト（入力・出力のビット反転なし、最終 XOR なし）で、生成多項式
    0x04C11DB7、初期値 0xFFFFFFFF を用いて 1 バイトずつ畳み込む。

    Args:
        data: CRC を計算する対象のバイト列。

    Returns:
        32 ビットの CRC 値（0 以上 0xFFFFFFFF 以下）。
    """
    crc: int = INIT
    byte: int
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ POLY) & MASK
            else:
                crc = (crc << 1) & MASK
    return crc

def self_test() -> None:
    """CRC 実装の正しさを標準チェック値で自己検証する。
    
    CRC-32/MPEG-2 はバイト列 ``b"123456789`` に対して 0x0376E6E7 を返すことが
    規格で定められている。一致しなければ実装の誤りとして異常終了する。

    Raises:
        SystemExit: 計算結果が標準チェック値と一致しない場合。
    """
    got: int = crc32_mpeg2(b"123456789")
    if got != CHECK_VALUE:
        sys.exit(f"自己検証失敗： crc32_mpeg2('123456789')=0x{got:08X} "
                 f"（期待 0x{CHECK_VALUE}）")

def build(raw: bytes) -> tuple[bytes, int]:
    """raw boot2 をパディングし、CRC を付加して 256 バイトのブロブにする。

    入力を 252 バイトまで 0x00 でパディングし、その 252 バイトに対する
    CRC-32/MPEG-2 を末尾 4 バイト（リトルエンディアン）として付加する。

    Args:
        raw: チェックサム前の boot2 バイト列（252 バイト以下）。

    Returns:
        生成した 256 バイトのブロブと、付加した CRC 値のタプル。

    Raises:
        SystemExit: 入力が 252 バイトを超える場合。
    """
    if len(raw) > PAYLOAD_SIZE:
        sys.exit(f"boot2 が大きすぎます：{len(raw)} バイト"
                 f"(CRC を除いた上限は {PAYLOAD_SIZE} バイト)")
    payload: bytes = raw + b"\x00" * (PAYLOAD_SIZE - len(raw))
    crc: int = crc32_mpeg2(payload)
    out: bytes = payload + struct.pack("<I", crc)   # 末尾にリトルエンディアンで付加
    assert len(out) == BOOT2_TOTAL
    return out, crc

def check(blob: bytes) -> int:
    """256 バイトの boot2 ブロブの整合性を検証する。

    サイズが 256 バイトであること、および末尾 4 バイトが先頭 252 バイトの
    CRC-32/MPEG-2 と一致することを確認する。

    Args:
        blob: 検証対象の boot2 バイト列。

    Returns:
        検証に成功すれば 0、失敗すれば 1（プロセスの終了コードに使う）。
    """
    if len(blob) != BOOT2_TOTAL:
        print(f"NG：サイズが {len(blob)} バイト（期待 {BOOT2_TOTAL}）")
        return 1
    expected: int = crc32_mpeg2(blob[:PAYLOAD_SIZE])
    stored: int = struct.unpack("<I", blob[PAYLOAD_SIZE:])[0]
    if expected != stored:
        print(f"NG：CRC 不一致 stored=0x{stored:08X} expected=0x{expected:08X}")
        return 1
    print(f"OK：256 バイト/ 末尾 CRC=0x{stored:08X} 一致")
    return 0

def main() -> None:
    """コマンドライン引数を解釈し、boot2 の生成または検証を実行する。
    
    通常モードでは入力 boot2 にチェックサムを付加して出力ファイルへ書き出す。
    ``--check`` モードでは入力を 256 バイトの boot2 として検証のみ行う。
    いずれのモードでも実行前に CRC 実装の自己検証を行う。

    Raises:
        SystemExit: 引数不足、入力サイズ超過、または検証失敗の場合。
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="boot2 に RP2040 bootrom 用 CRC32 チェックサムを付加する"
    )
    parser.add_argument("input", help="入力ファイル")
    parser.add_argument("output", nargs="?",
                        help="出力先（256B）。--check 時は不要")
    parser.add_argument("--check", action="store_true",
                        help="入力を 256B の boot2 として検証する（生成しない）")
    args: argparse.Namespace = parser.parse_args()

    self_test()

    with open(args.input, "rb") as f:
        data: bytes = f.read()

    if args.check:
        sys.exit(check(data))

    if not args.output:
        sys.exit("出力先を指定してください（--check でない場合は必須）")

    out: bytes
    crc: int
    out, crc = build(data)
    with open(args.output, "wb") as f:
        f.write(out)
    pad: int = PAYLOAD_SIZE - len(data)
    print(f"入力        ：{args.input}（{len(data)} バイト）")
    print(f"パディング   ：{PAYLOAD_SIZE} バイト（0x00 埋め {pad} バイト）")
    print(f"CRC32      ：0x{crc:08X}（CRC-32/MPEG-2）")
    print(f"出力        ：{args.output}（{BOOT2_TOTAL} バイト, 末尾4B=CRC LE）")

if __name__ == "__main__":
    main()
