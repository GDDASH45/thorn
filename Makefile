CC      := gcc
AS      := as
NASM    := nasm
LD      := ld
OBJCOPY := objcopy

CFLAGS  := -m32 -ffreestanding -fno-pic -fno-stack-protector
ASFLAGS := --32
LDFLAGS := -m elf_i386

SRC_C   :=
SRC_AS  := thorn-core/early.asm

OBJ_C   := $(SRC_C:.c=.o)
OBJ_AS  := $(SRC_AS:.asm=.o)
OBJ     := $(OBJ_C) $(OBJ_AS)

STAGE1  := build/stage1.bin
STAGE2  := build/stage2.bin
STAGE2_ELF := build/stage2.elf

.PHONY: all clean

all: $(STAGE1) $(STAGE2)

$(STAGE1): thorn-core/stage1.asm
	@mkdir -p build
	@echo "  NASM    $<"
	@$(NASM) -f bin $< -o $@

$(STAGE2_ELF): $(OBJ) thorn-core/stage2.ld
	@mkdir -p build
	@echo "  LD      $@"
	@$(LD) $(LDFLAGS) -T thorn-core/stage2.ld $(OBJ) -o $@

$(STAGE2): $(STAGE2_ELF)
	@echo "  OBJCOPY $<"
	@$(OBJCOPY) -O binary $< $@

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

clean:
	@echo "  CLEAN"
	@rm -rf build $(OBJ)
