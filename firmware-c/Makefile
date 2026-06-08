.PHONY: check clean docs docs-clean boot2

# ビルド成果物の出力先
BUILD_DIR := build

# クロスコンパイル設定（Cortex-M0+ / Thumb / ベアメタル）
ARM_CC		:= arm-none-eabi-gcc
ARM_CFLAGS	:= -mcpu=cortex-m0plus -mthumb -nostdlib -ffreestanding
ARM_INCLUDE	:= -I src/boot

check:
	@echo "=== Compiler check ==="
	@clang --version | head -1
	@arm-none-eabi-gcc --version | head -1
	@gdb-multiarch --version | head -1
	@echo ""
	@echo "=== Tools check ==="
	@arm-none-eabi-objcopy --version | head -1
	@arm-none-eabi-objdump --version | head -1
	@arm-none-eabi-readelf --version | head -1
	@arm-none-eabi-size --version | head -1
	@echo ""
	@echo "=== OpenOCD check ==="
	@openocd --version 2>&1 | head -1
	@echo "RP2040 target script:"
	@(ls /usr/share/openocd/scripts/target/rp2040.cfg 2>/dev/null && echo "  found") || echo "  NOT found (may need newer OpenOCD)"
	@echo ""
	@echo "=== svdconv check ==="
	@svdconv --version 2>&1 | head -2
	@echo ""
	@echo "=== Cross compile test (Clang -> Cortex-M0+) ==="
	@echo 'int main(void) { return 0; }' > /tmp/test.c
	@clang --target=arm-none-eabi \
	       -mcpu=cortex-m0plus \
	       -mthumb \
	       -nostdlib \
	       -ffreestanding \
	       -c /tmp/test.c \
	       -o /tmp/test.o
	@echo "Cross compile: OK"
	@arm-none-eabi-objdump -d /tmp/test.o | head -10
	@rm -f /tmp/test.c /tmp/test.o

# boot2（Boot Stage 2）を no-SDK でアセンブルする
# pico-sdk に依存せず、自前の rp2040_boot_regs.h と boot2_helpers/ のみで
# アセンブルできることを確認する。
# boot2 は 256 バイト固定（末尾 4 バイトはチェックサム）のため、
# 実コードは 252 バイト以内に収める必要がある。アセンブル後にサイズを表示する。
boot2:
	@mkdir -p $(BUILD_DIR)
	$(ARM_CC) $(ARM_CFLAGS) $(ARM_INCLUDE) \
		-c src/boot/boot2_w25q080.S \
		-o $(BUILD_DIR)/boot2.o
	@echo ""
	@echo "=== boot2 アセンブル成功 ==="
	@arm-none-eabi-size $(BUILD_DIR)/boot2.o
	@echo "(.text が 252 バイト以内であることを確認すること)"

# DoxygenでAPIドキュメントを生成
docs:
	mkdir -p docs/api
	doxygen Doxyfile
	@echo ""
	@echo "API documentation generated at docs/api/html/index.html"

# Doxygenが生成したファイルをクリーン
docs-clean:
	rm -rf docs/api

clean:
	rm -f /tmp/test.c /tmp/test.o
	rm -rf $(BUILD_DIR)
