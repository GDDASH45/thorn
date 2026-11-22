# Thorn architecture

This document describes the current implementation and the boundaries between
implemented behavior, protocol design, and future work. It is intentionally
conservative: a planned feature is not described as working merely because a
header or function declaration exists.

## Project goals

Thorn is an x86 BIOS bootloader. Its first target is a small, understandable
BIOS disk image that can be built with NASM, GCC, GNU binutils, and Make.

The implementation is split into a 16-bit first stage and a 32-bit second
stage. Stage 1 performs operations that require BIOS services. Stage 2 runs
freestanding C and assembly after the processor enters protected mode.

The project currently targets legacy BIOS boot from a raw disk image. UEFI,
long mode, filesystem parsing, kernel loading, and a real-mode thunk are not
current capabilities.

## Execution overview

The expected path through the current image is:

1. BIOS loads the first sector at physical address 0x7C00.
2. Stage 1 initializes real-mode segment registers and the stack.
3. Stage 1 stores the BIOS drive number from DL.
4. Stage 1 selects BIOS video mode 3.
5. Stage 1 verifies that INT 13h Extensions are present.
6. Stage 1 reads 32 sectors beginning at LBA 1 to physical address 0x8000.
7. Stage 1 enables A20 using the fast A20 gate.
8. Stage 1 loads the Global Descriptor Table.
9. Stage 1 sets CR0.PE and performs a far jump into 32-bit protected mode.
10. Stage 1 loads the flat data selectors and jumps to 0x8000.
11. Stage 2 establishes its own stack and calls thorn_main.
12. Stage 2 initializes the terminal and reports the current video fallback.
13. Stage 2 halts because kernel loading and the final handoff are not yet
    implemented.

The sequence above is the intended flow represented by the source. A successful
build alone does not prove that the image boots correctly on every BIOS.

## Stage 1

Stage 1 lives in thorn-core/stage1.asm. It is assembled as a flat binary and
must occupy exactly 512 bytes. The last two bytes are the 0xAA55 boot signature.

### Real-mode environment

The BIOS enters the boot sector in 16-bit real mode. The boot sector cannot
assume that DS, ES, SS, or the direction flag are already in a useful state.
Thorn explicitly initializes these values before using memory or string
instructions.

The stack is placed below the boot sector at 0x7C00 and grows downward. The
boot sector must not overwrite its own instructions or data while using that
stack.

The BIOS drive number is provided in DL. Thorn stores it before calling BIOS
services because firmware calls may change registers. The saved value is used
again for the EDD disk read.

### Text mode

Stage 1 requests BIOS video mode 3 through INT 10h. This is an 80-column by
25-row color text mode on conventional VGA-compatible firmware. Stage 2's
terminal writes character and attribute words to physical address 0xB8000.

This is a BIOS request, not a guarantee that every possible display adapter
behaves identically. The current implementation assumes a conventional VGA
text buffer.

### Disk access

Thorn uses INT 13h Extensions rather than CHS geometry. It checks the EDD
installation signature and capability bit before issuing AH=42h.

The Disk Address Packet describes a transfer of 32 sectors from LBA 1 into
0000:8000. One sector is 512 bytes, so the Stage 2 storage area is 16384 bytes.

The transfer buffer is below the conventional 1 MiB boundary. The DAP transfer
must remain within the constraints accepted by the BIOS. The current image
layout and fixed transfer count are designed to satisfy the common EDD BIOS
path, but unusual firmware should be tested separately.

A disk failure or missing EDD support is reported using BIOS teletype output,
after which Stage 1 halts. There is no retry policy yet.

### A20 and protected mode

Stage 1 enables A20 through port 0x92. It then loads the GDT descriptor, sets
the PE bit in CR0, and performs a far jump to reload CS with the code selector.

The GDT contains a null descriptor, a flat 32-bit code descriptor, and a flat
32-bit data descriptor. The code selector is 0x08 and the data selector is
0x10.

After the far jump, Stage 1 loads DS, ES, FS, GS, and SS with the data selector.
It then transfers control to 0x8000.

BIOS interrupts are not available as ordinary real-mode services after this
transition. Stage 2 must not attempt to call INT 10h or INT 13h directly.

## Stage 2

Stage 2 is linked at physical address 0x8000. The linker script places the
.text.entry input section before other text sections so that early_entry is
the first instruction in the flat binary.

The entry stub disables interrupts, sets ESP to the top of a reserved 16 KiB
stack, clears the direction flag, and calls thorn_main.

The current code does not install an IDT. Interrupts remain disabled. This is
deliberate for the early skeleton: enabling interrupts before a valid IDT and
interrupt-controller setup would make faults difficult to diagnose.

### Stack

The stack is reserved in the .bss section. A flat binary does not necessarily
contain bytes for .bss, so the runtime address is established by the linker
rather than by copying stack contents from disk.

The stack must remain below any memory region later used for the kernel,
boot information, memory map, or other temporary buffers. A future memory
layout document must assign non-overlapping ranges before loading a kernel.

### C runtime assumptions

Thorn is freestanding. It does not have a hosted C runtime, libc startup files,
dynamic linking, or an operating-system process environment.

Code must not assume that global constructors, TLS, environment variables,
file descriptors, or a standard process entry point exist.

The current Makefile disables position-independent code, stack protector
instrumentation, and compiler builtins. New compiler options must be checked
against the actual compiler and target.

## Linker layout

The linker script begins at 0x8000 and defines separate loadable program
headers for executable text, read-only data, and writable data.

The BIOS does not load the ELF program headers. The Makefile converts the
linked ELF file into a flat binary using objcopy. Therefore, the physical
ordering of allocated sections in the linker script is important.

The ELF file is useful for symbols and debugging. The flat binary is what
Stage 1 reads from disk.

The linker layout must keep the complete flat Stage 2 image within the 16 KiB
disk allocation. The build recipe checks this limit before assembling the disk
image.

## Terminal

The terminal is a small VGA text-mode output layer implemented in
thorn-core/terminal.h. It stores the current row and column, writes character
and attribute pairs, and updates the hardware cursor through ports 0x3D4 and
0x3D5.

Supported control characters are:

- Line feed: move to the next row.
- Carriage return: move to column zero.
- Backspace: erase the preceding character on the current row.
- Tab: advance to the next eight-column boundary.

When the cursor moves beyond the final row, the terminal scrolls the visible
buffer upward and clears the last row.

The implementation is intentionally small. It is not a terminal emulator and
does not parse ANSI escape sequences, UTF-8, or terminal control protocols.

The terminal uses a single fixed color attribute. Color management, alternate
screens, scrolling regions, and buffered output are future work.

## Video ownership

Thorn, not the kernel, owns video-mode selection during boot. The kernel should
inherit the selected mode and the framebuffer metadata through the boot
protocol.

Stage 1 currently selects text mode 3 while BIOS services are available.
Stage 2's graphics initializer returns failure because a VBE mode switch has
not yet been implemented. This is an honest fallback, not a partially working
graphics mode.

A future VBE implementation must run while BIOS video services can be called,
or use a carefully designed real-mode thunk. It must query mode information,
validate the returned framebuffer layout, set the mode, and pass the actual
framebuffer address, pitch, dimensions, and bits per pixel to the kernel.

A requested resolution is not evidence that the firmware selected that mode.

## Thorn Boot Protocol

The current register interface is documented in boot-protocol.md. The intended
kernel entry contract is:

- EAX contains the THRN magic value.
- EBX contains capability flags.
- ECX contains a pointer to the boot-information structure.

The handoff assembly routine exists, but no current code calls it. It is not
evidence that a kernel can already be loaded.

Capability bits must describe valid data. Do not set a flag simply because a
field exists in a C structure.

## Error handling

Stage 1 currently has a single fatal disk error path. Stage 2 has no structured
error system. It prints basic status messages and halts.

Future error handling should preserve the original failure reason, identify
the stage that detected it, and avoid attempting unsafe recovery after the
processor or memory state becomes uncertain.

A bootloader error should not silently continue with invalid pointers,
truncated data, or incomplete metadata.

## Security and robustness principles

The loader will eventually parse untrusted disk contents. Every size, offset,
count, address, and arithmetic operation must be validated before use.

A parser must reject truncated headers, integer overflow, overlapping regions
where overlap is forbidden, and data that exceeds the available memory range.

The kernel entry address must refer to a loaded executable region. The loader
must not jump to a value merely because it appears in a file header.

Disk input should be treated as hostile. Checksums can detect accidental
corruption but do not authenticate a kernel.

The loader should never describe an image as verified unless it has performed
the corresponding validation.

## Build and test separation

The Makefile builds the actual boot image. The Python utilities under tools/
inspect host-side files and do not participate in the boot path.

The host-side test suite exercises deterministic parsing and validation
functions. It cannot prove BIOS compatibility, real-mode correctness, or
successful execution in QEMU.

Use both host tests and emulator tests. Record which class of validation has
actually been performed when reporting a release.

## Non-goals for the current stage

The current stage does not implement:

- UEFI boot services.
- Long mode or 64-bit kernel entry.
- Filesystem discovery.
- FAT, ext2, ISO9660, or other filesystem parsing.
- Kernel file selection.
- ELF kernel loading into physical memory.
- E820 memory-map discovery.
- VBE graphics mode setup.
- A20 verification through alternate controller methods.
- Interrupt handling after protected-mode entry.
- SMP startup.
- Secure Boot or cryptographic signature verification.

These items may become roadmap work, but they must not be inferred from the
presence of protocol fields or helper declarations.
