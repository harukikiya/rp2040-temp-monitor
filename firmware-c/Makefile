.PHONY: check clean docs docs-clean boot2 verify-linker boot2-checksum

# ビルド成果物の出力先
BUILD_DIR := build

# クロスコンパイル設定（Cortex-M0+ / Thumb / ベアメタル）
# コンパイラは clang を使用する（プロジェクト方針）。
# clang は --target でクロスターゲットを指定する。
# objcopy / objdump / size などのバイナリユーティリティは
# Arm GNU Toolchain （arm-none-eabi-*）のものを使う。
ARM_CC		:= clang --target=arm-none-eabi
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

# リンカスクリプト rp2040.ld の静的検証（段階2-C-3-4）
# boot2 + 検証用プローブをリンクし、セクション配置・LMA/VMA・シンボルを確認する。
# crt0 実装前のため動作検証は行わない（静的検証のみ）。
verify-linker: boot2
	@mkdir -p $(BUILD_DIR)
	@echo "=== 検証用プローブのコンパイル ==="
	$(ARM_CC) $(ARM_CFLAGS) $(ARM_INCLUDE) \
		-c verify/linker_probe.c \
		-o $(BUILD_DIR)/linker_probe.o
	@echo "=== リンク（rp2040.ld 適用） ==="
	arm-none-eabi-ld -T src/linker/rp2040.ld \
		$(BUILD_DIR)/boot2.o $(BUILD_DIR)/linker_probe.o \
		-o $(BUILD_DIR)/firmware.elf
	@echo "リンク成功: $(BUILD_DIR)/firmware.elf"
	@echo ""
	@echo "=== [1] セクション配置（.boot2=0x10000000, .vector=0x10000100 を確認） ==="
	arm-none-eabi-readelf -S $(BUILD_DIR)/firmware.elf
	@echo ""
	@echo "=== [2] LMA/VMA 分離（.data の VMA=RAM, LMA=FLASH を確認） ==="
	arm-none-eabi-objdump -h $(BUILD_DIR)/firmware.elf
	@echo ""
	@echo "=== [3] リンカ生成シンボル ==="
	@arm-none-eabi-nm $(BUILD_DIR)/firmware.elf | grep -E \
		"__etext|__data_start__|__data_end__|__bss_start__|__bss_end__|__StackTop|__StackBottom" \
		|| echo "（一部シンボル未検出 - 確認が必要）"
	@echo ""
	@echo "=== [4] .vectors の配置内容 ==="
	arm-none-eabi-objdump -s -j .vectors $(BUILD_DIR)/firmware.elf
	@echo ""
	@echo "=== [5] メモリ使用量 ==="
	arm-none-eabi-size $(BUILD_DIR)/firmware.elf

# boot2 に CRC32 チェックサムを付加し、焼ける 256 バイトのブロブを生成する（段階2-C-3-5）
# RP2040 の bootrom は先頭 252 バイトの CRC-32/MPEG-2 を末尾 4 バイトと照合する。
# 不一致だと boot2 を実行せず USB ブートローダ（RPI-RP2）に落ちる。
# boot2.o の .boot2 セクションを raw 抽出 → pad_checksum.py で CRC 付加する。
# 注：boot2 が再配置（リロケーション）を持たない自己完結アセンブリである前提。
# 	外部シンボル参照を入れた場合は単独リンク（ld）が必要になる。
BOOT2_RAW	:= $(BUILD_DIR)/boot2.raw.bin
BOOT2_BIN	:= $(BUILD_DIR)/boot2_checksummed.bin

boot2-checksum: boot2
	@echo ""
	@echo "=== [1] boot2 raw 抽出（.boot2 セクション） ==="
	arm-none-eabi-objcopy -O binary -j .boot2 \
		$(BUILD_DIR)/boot2.o $(BOOT2_RAW)
	@echo "raw boot2：$$(wc -c < $(BOOT2_RAW)) バイト（252 以内であること）"
	@echo ""
	@echo "=== [2] CRC32 付加（CRC-32/MPEG-2 → 256 バイト固定） ==="
	python3 tools/pad_checksum.py $(BOOT2_RAW) $(BOOT2_BIN)
	@echo ""
	@echo "=== [3] 出力検証（サイズ・末尾 CRC 一致、不一致で nonzero） ==="
	python3 tools/pad_checksum.py --check $(BOOT2_BIN)

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
