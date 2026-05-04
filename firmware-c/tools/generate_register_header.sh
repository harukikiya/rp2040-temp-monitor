#!/bin/bash
# RP2040.svd から C ヘッダを生成するスクリプト
#
# 使用方法:
#   /workspace/tools/generate_register_header.sh
#
# 前提:
#   svdconv がPATHに入っていること
#
# 入力:
#   /workspace/svd/RP2040.svd
# 出力:
#   /workspace/include/generated/RP2040.h
#   /workspace/include/generated/svdconv.log
#
# 注意:
#   svdconvは M381 エラー(SPARE_IRQ番号がdeviceNumInterruptsを超える)を
#   6個報告して非0終了するが、ヘッダは正しく生成される。
#   詳細はsvdconv.logを参照。

SVD_FILE="/workspace/svd/RP2040.svd"
OUTPUT_DIR="/workspace/include/generated"

# 入力ファイルチェック
if [ ! -f "$SVD_FILE" ]; then
    echo "Error: SVD file not found at $SVD_FILE"
    exit 1
fi

# svdconvの存在チェック
if ! command -v svdconv > /dev/null 2>&1; then
    echo "Error: svdconv not found in PATH"
    echo "This script must be run inside firmware-c dev container."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

echo "Generating C header from $SVD_FILE..."

# svdconvを実行(M381エラーで非0終了するが構わない)
svdconv "$SVD_FILE" \
    --generate=header \
    --fields=macro \
    --log=svdconv.log

# 生成されたか確認
if [ -f "$OUTPUT_DIR/RP2040.h" ]; then
    LINES=$(wc -l < "$OUTPUT_DIR/RP2040.h")
    echo ""
    echo "Generation complete."
    echo "  Output: $OUTPUT_DIR/RP2040.h ($LINES lines)"
    echo "  Log:    $OUTPUT_DIR/svdconv.log"
    echo ""
    echo "Note: M381 errors about SPARE_IRQ are expected and can be ignored."
    exit 0
else
    echo ""
    echo "Error: RP2040.h was not generated."
    echo "Check $OUTPUT_DIR/svdconv.log for details."
    exit 1
fi