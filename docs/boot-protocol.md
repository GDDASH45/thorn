# Thorn Boot Protocol (TBP)

TBP is the register-based interface used when Thorn transfers control to a
32-bit kernel entry point.

## Entry registers

At the kernel entry address:

| Register | Meaning |
| --- | --- |
| `EAX` | Magic value `0x5448524E` (`THRN`) |
| `EBX` | TBP capability flags |
| `ECX` | Physical address of `struct thorn_boot_info` |

The entry point is entered with a near jump from 32-bit protected mode. The
kernel entry stub should capture these registers before calling ordinary C
code; a C function prologue is not required to preserve the boot registers.

## Flags

| Flag | Value | Meaning |
| --- | ---: | --- |
| `THORN_FLAG_MEMORY_MAP` | `0x01` | Memory-map fields are valid |
| `THORN_FLAG_BOOT_DRIVE` | `0x02` | BIOS boot-drive field is valid |
| `THORN_FLAG_FRAMEBUFFER` | `0x04` | Framebuffer fields are valid |
| `THORN_FLAG_KERNEL` | `0x08` | Kernel image metadata is valid |

The combined mode values are currently defined as:

- Text mode: `0x03` (memory map + boot drive)
- Graphics mode: `0x07` (memory map + boot drive + framebuffer)

These values describe the expected flags once those capabilities are actually
implemented. Thorn must not set a capability bit merely because a field or
constant exists; the corresponding data must be populated and valid.

## Boot information

The C structure is declared in `thorn-core/boot.h`:

- `boot_drive`: BIOS drive number (for example, `0x80`).
- `memory_map_address`: physical address of the memory-map buffer.
- `memory_map_entries`: number of valid memory-map entries.
- `kernel_address`: physical load address of the kernel image.
- `kernel_size`: size of the loaded kernel in bytes.
- `framebuffer_address`: physical framebuffer address.
- `framebuffer_width`, `framebuffer_height`: framebuffer dimensions.
- `framebuffer_pitch`: bytes per framebuffer scanline.
- `framebuffer_bpp`: bits per pixel.

All addresses in this 32-bit protocol are physical addresses. Fields whose
capability flag is clear must be treated as unavailable by the kernel.

## Current implementation status

The register handoff routine exists, but Thorn does not yet load a kernel or
invoke it. Memory-map discovery, boot-drive propagation, and framebuffer
initialization are also not yet implemented. Stage 1 currently establishes
BIOS text mode 3; Stage 2 cannot invoke BIOS VBE services after entering
protected mode without a real-mode thunk or a separate real-mode setup stage.
