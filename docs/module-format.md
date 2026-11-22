# Thorn raw module format

Thorn uses the .mod extension for its version 1 raw machine-code module
container. A module contains a fixed 32-byte header followed immediately by
its machine-code payload.

The payload is raw 32-bit i386 code. It is not an ELF object, shared library,
or relocatable object file. Version 1 requires position-independent code and
does not define a relocation table.

## File layout

All multi-byte fields are little-endian.

| Offset | Size | Field | Version 1 value or meaning |
| ---: | ---: | --- | --- |
| 0 | 8 | Magic | THRNMOD followed by NUL |
| 8 | 2 | Format version | 1 |
| 10 | 2 | Header size | 32 |
| 12 | 2 | Architecture | 3 (i386) |
| 14 | 2 | Flags | Bit 0: position-independent payload |
| 16 | 4 | Payload size | Number of raw code bytes |
| 20 | 4 | Entry offset | Offset of the module entry point within the payload |
| 24 | 4 | Payload CRC-32 | CRC-32/ISO-HDLC of the payload |
| 28 | 4 | Reserved | Must be zero |
| 32 | variable | Payload | Raw i386 machine code |

The magic is eight bytes: the seven ASCII characters THRNMOD followed by
a NUL byte. The header structure is also declared in include/module.h.

## Validation rules

A valid version 1 module must satisfy all of the following:

- The file contains the complete 32-byte header.
- The magic, format version, header size, and architecture match this
  specification.
- The position-independent flag is set and no unknown flag bits are set.
- The reserved field is zero.
- The payload is non-empty.
- The file contains exactly the number of payload bytes declared in the
  header; truncated data and trailing bytes are rejected.
- The entry offset is strictly smaller than the payload size.
- The stored CRC-32 matches the payload.

CRC-32 detects accidental corruption. It does not authenticate a module or
make untrusted machine code safe to execute.

## Machine-code requirements

Version 1 modules contain raw i386 machine code, not ELF relocatable objects.
The payload must be position-independent because the format has no relocation
records and does not prescribe a fixed physical load address.

The entry offset is relative to the first payload byte. Once a loader places
the payload at address base, the entry address is base + entry_offset.

The version 1 module execution ABI, including entry registers, execution
context, service callbacks, and return codes, is specified in
[module-abi.md](module-abi.md). The ABI is a separate contract from the file
container. Thorn's current boot path does not yet load or execute .mod files.

## Creating a module

First produce a flat binary containing position-independent i386 machine
code. For example, NASM can assemble a flat binary directly:

~~~sh
nasm -f bin module.asm -o module.bin
~~~

Package it as a Thorn module:

~~~sh
python3 tools/pack-mod.py module.bin module.mod --entry-offset 0
~~~

The entry offset may be written in decimal or with a 0x prefix.

Inspect and validate the resulting file:

~~~sh
python3 tools/inspect-mod.py module.mod
python3 tools/inspect-mod.py --json module.mod
~~~

The host tools validate the container and checksum. They do not prove that
the machine code is position-independent or safe to execute.

The TBP command module source is modules/tbp.asm. Build it with make modules;
the packaged module is written to build/tbp.mod.
