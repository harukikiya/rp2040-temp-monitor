#!/usr/bin/env python3
"""ベクタテーブルの内容を機械検証する（verify-linker の一部）。

firmware.elf から .vectors セクションの実バイトを抽出し、シンボルテーブルと
突き合わせて以下を検査する:

    V1: .vectors のサイズが 192 バイト（48 エントリ × 4 バイト）であること
    V2: vector[0] == __StackTop（初期スタックポインタ）
    V3: vector[1] == Reset_Handler | 1（Thumb ビット付きのリセットベクタ）

boot2 は vector[0] を SP にロードし vector[1] へ分岐するため、この2エントリの
誤りは「一切起動しない」に直結する。目視確認を機械化し、CI で退行を検出する。

使い方:
    python3 verify/check_vectors.py build/firmware.elf

終了コード:
    0 = 全チェック PASS ／ 1 = いずれか FAIL ／ 2 = 入力・環境の不備
"""
from __future__ import annotations

import struct
import subprocess
import sys
import tempfile

VECTOR_ENTRIES: int = 48                    # システム例外 16 + 外部 IRQ 32
VECTOR_SIZE: int = VECTOR_ENTRIES * 4       # 192 バイト
THUMB_BIT: int = 1                          # 関数アドレスに立つ Thumb ビット

NM: str = "arm-none-eabi-nm"
OBJCOPY: str = "arm-none-eabi-objcopy"


def read_symbols(elf: str) -> dict[str, int]:
    """nm でシンボルテーブルを読み、名前→アドレスの辞書にする。

    Args:
        elf: 対象 ELF ファイルのパス。

    Returns:
        シンボル名をキー、アドレス（int）を値とする辞書。

    Raises:
        SystemExit: nm の実行に失敗した場合（終了コード 2）。
    """
    try:
        out: str = subprocess.check_output([NM, elf], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.exit(f"nm の実行に失敗: {e}")
    syms: dict[str, int] = {}
    for line in out.splitlines():
        parts: list[str] = line.split()
        if len(parts) == 3:
            syms[parts[2]] = int(parts[0], 16)
    return syms


def read_vectors(elf: str) -> bytes:
    """objcopy で .vectors セクションの実バイトを抽出する。

    Args:
        elf: 対象 ELF ファイルのパス。

    Returns:
        .vectors の生バイト列。

    Raises:
        SystemExit: objcopy の実行に失敗した場合（終了コード 2）。
    """
    with tempfile.NamedTemporaryFile(suffix=".bin") as tmp:
        try:
            subprocess.check_call(
                [OBJCOPY, "-O", "binary", "-j", ".vectors", elf, tmp.name])
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            sys.exit(f"objcopy の実行に失敗: {e}")
        with open(tmp.name, "rb") as f:
            return f.read()


def main() -> None:
    """検査を実行し、結果を表示して終了コードで返す。

    Raises:
        SystemExit: 検査結果に応じた終了コード（モジュール docstring 参照）。
    """
    if len(sys.argv) != 2:
        sys.exit("使い方: check_vectors.py <firmware.elf>")
    elf: str = sys.argv[1]

    syms: dict[str, int] = read_symbols(elf)
    vec: bytes = read_vectors(elf)
    fail: int = 0

    # V1: サイズ
    if len(vec) == VECTOR_SIZE:
        print(f"OK：.vectors サイズ = {len(vec)} バイト（48 エントリ）")
    else:
        print(f"NG：.vectors サイズ = {len(vec)} バイト（期待 {VECTOR_SIZE}）")
        fail = 1

    # V2 / V3 に必要なシンボルの存在確認
    required: list[str] = ["__StackTop", "Reset_Handler"]
    missing: list[str] = [s for s in required if s not in syms]
    if missing:
        print(f"NG：シンボル未検出: {', '.join(missing)}")
        sys.exit(1)

    if len(vec) >= 8:
        entry0: int = struct.unpack_from("<I", vec, 0)[0]
        entry1: int = struct.unpack_from("<I", vec, 4)[0]

        # V2: 初期 SP
        expected_sp: int = syms["__StackTop"]
        if entry0 == expected_sp:
            print(f"OK：vector[0] = 0x{entry0:08X} == __StackTop")
        else:
            print(f"NG：vector[0] = 0x{entry0:08X}（期待 __StackTop = 0x{expected_sp:08X}）")
            fail = 1

        # V3: Reset（Thumb ビット付き）
        expected_reset: int = syms["Reset_Handler"] | THUMB_BIT
        if entry1 == expected_reset:
            print(f"OK：vector[1] = 0x{entry1:08X} == Reset_Handler|1")
        else:
            print(f"NG：vector[1] = 0x{entry1:08X}"
                  f"（期待 Reset_Handler|1 = 0x{expected_reset:08X}）")
            fail = 1

    sys.exit(fail)


if __name__ == "__main__":
    main()