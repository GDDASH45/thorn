# TBP metadata validation

The host-side module tools/bootinfo.py provides a reference decoder and
validator for the current Thorn Boot Protocol information structure.

It is a development utility. It does not run in Stage 2 and does not change the
register ABI described in boot-protocol.md.

## Structure layout

The structure currently contains ten consecutive 32-bit unsigned integers.
Its packed size is 40 bytes.

| Field index | Field | Meaning |
| ---: | --- | --- |
| 0 | boot_drive | BIOS drive identifier |
| 1 | memory_map_address | Physical address of memory map |
| 2 | memory_map_entries | Number of map entries |
| 3 | kernel_address | Physical address of loaded kernel |
| 4 | kernel_size | Loaded kernel size in bytes |
| 5 | framebuffer_address | Physical framebuffer address |
| 6 | framebuffer_width | Visible pixel width |
| 7 | framebuffer_height | Visible pixel height |
| 8 | framebuffer_pitch | Bytes per framebuffer row |
| 9 | framebuffer_bpp | Bits per pixel |

The fields are encoded as little-endian 32-bit values. The host-side parser
requires at least 40 bytes. It ignores bytes after the structure so a caller
can decode this fixed prefix from a larger boot-information allocation.

## Register values

The entry point receives three values:

- EAX: magic 0x5448524E.
- EBX: capability flags.
- ECX: physical address of the structure.

The current structure definition is in thorn-core/boot.h. Keep the C layout
and the host-side Python layout synchronized if fields are added or reordered.

A protocol change should update the documentation and tests in the same
change. Do not silently change field widths or endianness.

## Capability semantics

A set flag promises that the corresponding fields are populated and usable.
A clear flag means the kernel must not rely on those fields.

The host-side validator checks these relationships:

- Memory-map flag requires a nonzero address and entry count.
- Boot-drive flag requires a nonzero BIOS drive value.
- Framebuffer flag requires a complete description and a pitch large enough
  for one visible row.
- Kernel flag requires a nonzero load address and nonzero image size.
- Fields belonging to a clear capability must remain zero.
- Unknown flag bits are rejected.

These checks are a strict development contract. If a future protocol version
needs optional or partial metadata, define that behavior explicitly rather
than weakening the validator without documentation.

## Framebuffer pitch

For a packed pixel format, the minimum bytes per row is:

`width * ceil(bits_per_pixel / 8)`

The pitch may be larger because firmware can add padding at the end of each
scanline. The validator accepts a pitch larger than the minimum and rejects
one that is too small.

This check does not validate pixel channel masks, reserved bits, color order,
or the total framebuffer memory range. Those fields are not currently part
of the TBP structure.

## Memory-map limitations

The current structure stores an address and entry count but does not define
the memory-map entry format in the C header. A later protocol revision should
define the entry structure, size, versioning, and lifetime.

The address must refer to memory that remains readable by the kernel after
handoff. The bootloader must not reuse the buffer before the kernel has
consumed it.

## Validation command

The Python module can be used by other host-side scripts:

```python
from tools.bootinfo import (
    BootContext,
    BootInfo,
    FLAG_BOOT_DRIVE,
    TBP_MAGIC,
    validate_context,
)

info = BootInfo(
    boot_drive=0x80,
    memory_map_address=0,
    memory_map_entries=0,
    kernel_address=0,
    kernel_size=0,
    framebuffer_address=0,
    framebuffer_width=0,
    framebuffer_height=0,
    framebuffer_pitch=0,
    framebuffer_bpp=0,
)
validate_context(BootContext(TBP_MAGIC, FLAG_BOOT_DRIVE, info))
```

The current bootloader does not yet populate a complete context, so this
example is a protocol-validation example rather than a description of the
current boot sequence.
