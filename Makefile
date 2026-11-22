CC      := gcc
AS      := as
NASM    := nasm
LD      := ld
OBJCOPY := objcopy

CFLAGS  := -m32 -ffreestanding -fno-pic -fno-stack-protector -fno-builtin -MMD -MP
ASFLAGS := --32
LDFLAGS := -m elf_i386

SRC_C   := thorn-core/main.c thorn-core/video.c
SRC_AS  := thorn-core/early.asm thorn-core/handoff.asm

OBJ_C   := $(SRC_C:.c=.o)
OBJ_AS  := $(SRC_AS:.asm=.o)
OBJ     := $(OBJ_C) $(OBJ_AS)

DEP     := $(OBJ_C:.o=.d)

STAGE1      := build/stage1.bin
STAGE2_ELF  := build/stage2.elf
STAGE2      := build/stage2.bin
BIOS_IMG    := build/boot-bios.img

.PHONY: all test clean

all: $(BIOS_IMG)

test:
	@echo "  TEST    host-side validation suite"
	@python3 -m unittest discover -s tests -v

$(STAGE1): thorn-core/stage1.asm
	@mkdir -p build
	@echo "  NASM    $<"
	@$(NASM) -f bin $< -o $@
	@test $$(stat -c%s $@) -eq 512

$(STAGE2_ELF): $(OBJ) thorn-core/stage2.ld
	@mkdir -p build
	@echo "  LD      $@"
	@$(LD) $(LDFLAGS) -T thorn-core/stage2.ld $(OBJ) -o $@

$(STAGE2): $(STAGE2_ELF)
	@echo "  OBJCOPY $<"
	@$(OBJCOPY) -O binary $< $@
	@test $$(stat -c%s $@) -le 16384

$(BIOS_IMG): $(STAGE1) $(STAGE2)
	@echo "  IMAGE   $@"
	@cat $(STAGE1) > $@
	@dd if=$(STAGE2) of=$@ bs=512 seek=1 conv=notrunc status=none
	@truncate -s 16896 $@

%.o: %.c
	@echo "  CC      $<"
	@$(CC) $(CFLAGS) -c $< -o $@

%.o: %.S
	@echo "  AS      $<"
	@$(CC) $(CFLAGS) -c $< -o $@

%.o: %.s
	@echo "  AS      $<"
	@$(AS) $(ASFLAGS) $< -o $@

%.o: %.asm
	@echo "  NASM    $<"
	@$(NASM) -f elf32 $< -o $@

-include $(DEP)

clean:
	@echo "  CLEAN"
	@rm -rf build $(OBJ) $(DEP)
