.PHONY: check clean

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

clean:
	rm -f /tmp/test.c /tmp/test.o