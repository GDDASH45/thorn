# SPDX-License-Identifier: GPL-2.0-or-later

CC      := gcc
AS      := as
NASM    := nasm
LD      := ld
OBJCOPY := objcopy

VERSION_MAJOR := 0
VERSION_MINOR := 1
VERSION_PATCH := 0
EXTRA_VERSION := -rc1

VERSION := $(VERSION_MAJOR).$(VERSION_MINOR).$(VERSION_PATCH)$(EXTRA_VERSION)

CFLAGS  := -m32 -ffreestanding -fno-pic -fno-stack-protector -fno-builtin -MMD -MP -Iinclude
ASFLAGS := --32
LDFLAGS := -m elf_i386

SRC_C   := thorn-core/main.c thorn-core/video.c thorn-core/err.c
SRC_AS  := thorn-core/early.asm thorn-core/handoff.asm

OBJ_C   := $(SRC_C:.c=.o)
OBJ_AS  := $(SRC_AS:.asm=.o)
OBJ     := $(OBJ_C) $(OBJ_AS)

DEP     := $(OBJ_C:.o=.d)

STAGE1      := build/stage1.bin
STAGE2_ELF  := build/stage2.elf
STAGE2      := build/stage2.bin
BIOS_IMG    := build/boot-bios.img
VER_HEADER  := include/generated/version.h

.PHONY: all test clean

all: $(BIOS_IMG)

test:
	@echo "  TEST    host-side validation suite"
	@python3 -m unittest discover -s tests -v

$(STAGE1): thorn-core/stage1.asm
	@mkdir -p $(dir $@)
	@echo "  NASM    $<"
	@$(NASM) -f bin $< -o $@
	@test $$(stat -c%s $@) -eq 512

$(VER_HEADER):
	@mkdir -p $(dir $@)
	@echo "  GEN     $@"
	@printf '%s\n' \
		'#ifndef VERSION_H' \
		'#define VERSION_H' \
		'' \
		'#define THORN_VERSION "$(VERSION)"' \
		'#define THORN_VERSION_MAJOR $(VERSION_MAJOR)' \
		'#define THORN_VERSION_MINOR $(VERSION_MINOR)' \
		'#define THORN_VERSION_PATCH $(VERSION_PATCH)' \
		'' \
		'#endif' > $@

$(OBJ_C): $(VER_HEADER)

$(STAGE2_ELF): $(OBJ) thorn-core/stage2.ld
	@mkdir -p $(dir $@)
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
	@rm -rf build $(OBJ) $(DEP) $(VER_HEADER)
