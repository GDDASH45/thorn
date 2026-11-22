# Thorn BIOS disk and memory layout

## Raw disk layout

The current image uses a fixed-size raw layout:

| Region | LBA | Byte offset | Size |
| --- | ---: | ---: | ---: |
| Stage 1 boot sector | 0 | 0 | 512 bytes |
| Stage 2 storage | 1-32 | 512 | 16384 bytes |
| End of image | — | 16896 | — |

The total image size is 16896 bytes, or 33 sectors.

The BIOS loads the first sector to physical address 0x7C00. Stage 1 then uses
EDD to read 32 sectors beginning at LBA 1 into physical address 0x8000.

## Sector arithmetic

The sector size is 512 bytes.

Stage 2 capacity is:

`32 * 512 = 16384 bytes`

The complete image size is:

`(1 + 32) * 512 = 16896 bytes`

The Stage 2 transfer begins at byte offset 512 in the disk image. Its memory
destination is 0x8000.

The disk offset and physical destination are separate concepts. LBA 1 is not
the same thing as physical address 0x8000; the DAP connects the two by
describing the source sectors and destination buffer.

## Disk Address Packet

Stage 1 uses the 16-byte EDD Disk Address Packet format:

| Offset | Width | Field |
| ---: | ---: | --- |
| 0 | 1 | Packet size, 0x10 |
| 1 | 1 | Reserved, zero |
| 2 | 2 | Sector count |
| 4 | 2 | Buffer offset |
| 6 | 2 | Buffer segment |
| 8 | 8 | Starting LBA |

The current packet requests 32 sectors, uses buffer segment 0 and offset
0x8000, and begins at LBA 1.

The BIOS interface expects little-endian fields. NASM's `dw` and `dq`
directives emit the values in the required little-endian byte order on x86.

## Stage 1 memory

The BIOS boot sector is loaded at 0x7C00. The real-mode stack pointer is
initialized to 0x7C00 with SS set to zero, so the stack grows downward from
that address.

The first stage stores its boot-drive byte in its own boot-sector data area.
That value is not currently copied into the Stage 2 boot-information
structure.

## Stage 2 memory

Stage 2 is loaded at 0x8000. The linker script begins its location counter at
that address.

The entry point is early_entry. It sets ESP to stack_top, which is reserved
in .bss. The stack reservation is 16 KiB and is aligned to 16 bytes.

The flat Stage 2 binary contains allocated loadable sections. The .bss
reservation is represented by addresses and sizes in the ELF file and does
not need to occupy bytes in the raw file.

## Memory ownership rules

The current code has not yet implemented a complete physical-memory map.
Future work must assign explicit ownership to:

- Stage 1's loaded boot sector.
- Stage 2's loaded image.
- The Stage 2 stack.
- The boot-information structure.
- Any E820 memory-map buffer.
- Temporary disk buffers.
- The kernel's destination ranges.
- The framebuffer, if graphics mode is initialized.

No two live objects may occupy overlapping physical memory unless the
overlap is explicitly part of a documented transfer or lifetime rule.

## Address-width limits

The current protected-mode code is 32-bit. The current boot protocol stores
physical addresses in 32-bit fields.

A future implementation must reject addresses that cannot be represented
without truncation. It must also check end addresses using overflow-safe
arithmetic before copying data into memory.

The present design does not support loading a 64-bit kernel above the 4 GiB
boundary.

## Changing the disk layout

Changing the Stage 2 sector count requires coordinated updates to:

1. The DAP sector count in stage1.asm.
2. The maximum Stage 2 size assertion in the Makefile.
3. The disk-image composition recipe.
4. The image-size constants in tools/thorn_image.py.
5. The tests and documentation.

Changing only one of these values can produce an image that builds but cannot
boot correctly.

A future variable-size loader may store a sector count in a header or use a
filesystem. That is not the current design.
