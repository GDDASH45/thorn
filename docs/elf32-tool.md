# ELF32 host inspection utility

The file tools/elf32.py implements a restricted parser for host-side inspection
of 32-bit little-endian i386 executable files.

It is intended to support development and testing of a future kernel-loading
path. It is not currently part of the Stage 2 boot path.

## Supported input

The parser accepts ELF files with these properties:

- ELF magic is 0x7F followed by ELF.
- ELF class is ELFCLASS32.
- Data encoding is little-endian.
- Identification version is current.
- File type is ET_EXEC.
- Machine is EM_386.
- ELF version is current.
- At least one PT_LOAD segment exists.
- The entry point is inside an executable PT_LOAD segment.

The parser does not currently accept ELF64, big-endian ELF, shared objects,
relocatable objects, or non-i386 architectures.

## Structural checks

The parser checks that the ELF header is present and that the reported header
size is not smaller than the required ELF32 header.

It checks the program-header entry size before stepping through the table.
It then verifies that the complete program-header table fits inside the file.

For each PT_LOAD segment, it verifies:

- File size does not exceed memory size.
- The file-backed range ends within the input file.
- The physical memory range does not overflow the 32-bit address space.
- Alignment is zero, one, or a power of two.
- Virtual address and file offset satisfy the declared alignment.

The parser then requires at least one loadable segment and verifies that the
entry point is inside an executable loadable segment.

## Program-header fields

The utility reports:

- Segment type.
- File offset.
- Virtual address.
- Physical address.
- File size.
- Memory size.
- Permission flags.
- Alignment.

The R, W, and X flags are displayed as a compact permission string.

## Command-line use

Run:

```sh
python3 tools/inspect-elf.py build/stage2.elf
```

For machine-readable output:

```sh
python3 tools/inspect-elf.py --json build/stage2.elf
```

The JSON output includes the file size, entry point, machine identifier, and
all loadable segment fields.

## Parser boundaries

This parser is intentionally not a kernel loader. It does not:

- Allocate physical memory.
- Copy PT_LOAD data to physical addresses.
- Zero memory beyond p_filesz.
- Choose a kernel load address.
- Relocate an executable.
- Process dynamic linking.
- Apply relocation records.
- Validate a complete physical-memory map.
- Check that segments avoid the bootloader or its stack.
- Enter the ELF entry point.
- Authenticate the file.

Those operations require a boot-time memory allocator and a complete memory
ownership design. Parsing a valid ELF header is only one step in safely
loading a kernel.

## Security considerations

ELF files are input data and must be treated as untrusted. Bounds checks are
performed before reading program-header entries or accepting segment ranges.

The parser does not claim that an ELF file is safe to execute. A structurally
valid executable can still contain malicious code or request memory that is
not suitable for the bootloader's current layout.

Checksums and signatures are separate concerns. A checksum can detect
accidental changes but cannot establish publisher identity. Authentication
requires a defined trust model and cryptographic verification.
