# Thorn testing guide

This guide separates tests that can run on a normal development host from
tests that require an emulator or real firmware.

## Test categories

Thorn has several distinct validation layers:

1. Source-level checks: formatting, syntax, and review.
2. Host-side unit tests: deterministic Python parsing and image checks.
3. Build checks: assembly, compilation, linking, and image-size limits.
4. Emulator checks: BIOS execution and visible boot behavior.
5. Firmware compatibility checks: behavior across different BIOS
   implementations and storage configurations.

Passing one category does not imply that the others pass.

## Required host tools

The boot image build requires:

- GNU Make.
- NASM.
- GCC with 32-bit freestanding compilation support.
- GNU binutils, including ld and objcopy.
- Standard shell utilities used by the Makefile.

The host-side validation tools use Python 3 and the standard library only.
No third-party Python package is required.

## Running the unit tests

From the repository root, run:

```sh
make test
```

The equivalent command is:

```sh
python3 -m unittest discover -s tests -v
```

The test suite should run without NASM, GCC, QEMU, root privileges, or access
to a physical disk. It creates temporary files only when a test needs a file
path.

## Image inspection

After building the image, inspect it with:

```sh
python3 tools/inspect-image.py build/boot-bios.img
```

For automation, use JSON output:

```sh
python3 tools/inspect-image.py --json build/boot-bios.img
```

The image inspector checks the fixed image size and the 0xAA55 signature.
It reports the number of non-zero bytes in the Stage 2 area, but that count is
not the exact Stage 2 binary size: valid binary data may end in zero bytes and
the disk image is padded to a fixed capacity.

The build system's Stage 2 size check is authoritative for the actual binary
before it is written into the image.

## ELF inspection

The ELF inspection tool reads a 32-bit little-endian i386 executable:

```sh
python3 tools/inspect-elf.py build/stage2.elf
```

It reports the entry point and loadable program headers. The parser rejects
unsupported classes, byte orders, machines, file types, malformed tables,
invalid segment bounds, and an entry point outside executable loadable data.

This tool is a host-side structural checker. It does not prove that a BIOS
loads the ELF file. Thorn's current BIOS path loads a flat binary generated
from the ELF file.

## Building the image

Run:

```sh
make
```

A successful build should produce:

```text
build/stage1.bin
build/stage2.elf
build/stage2.bin
build/boot-bios.img
```

The first stage must be exactly 512 bytes. The Stage 2 binary must not exceed
16384 bytes. The raw image is padded to 16896 bytes.

A failed assembler, compiler, linker, objcopy operation, or size assertion
must cause Make to fail. Do not ignore a failed command and continue with an
old image.

## QEMU smoke test

A basic BIOS smoke test can be performed with:

```sh
qemu-system-i386 -drive format=raw,file=build/boot-bios.img
```

The expected current behavior is:

- Firmware loads the boot sector.
- Stage 1 selects text mode and reads Stage 2.
- Stage 1 enters protected mode.
- Stage 2 prints its banner and status messages.
- The machine halts after the current initialization skeleton.

The current image does not load an operating-system kernel. A halt after the
Stage 2 status output is therefore expected.

For repeatable automated testing, use a timeout around QEMU and capture its
exit status. A timeout is not necessarily a boot failure because the current
program deliberately halts forever.

## Debugging with QEMU

QEMU can expose a GDB stub:

```sh
qemu-system-i386 -S -s -drive format=raw,file=build/boot-bios.img
```

In another terminal, connect GDB:

```sh
gdb
```

Then:

```gdb
target remote :1234
break *0x7c00
continue
```

The exact debugger setup depends on the symbols and whether the debugger is
attached before firmware execution. Stage 1 is a flat binary, so source-level
debugging requires a suitable symbol file or manually assigned addresses.

The Stage 2 ELF file contains symbols and is useful for debugging code linked
at 0x8000. The actual Stage 2 runtime address must match the linker script.

## Useful build inspection commands

Inspect the ELF header:

```sh
readelf -h build/stage2.elf
```

Inspect program headers:

```sh
readelf -l build/stage2.elf
```

Inspect symbols:

```sh
nm -n build/stage2.elf
```

Inspect the flat binary size:

```sh
stat -c '%s bytes' build/stage2.bin
```

Inspect the boot signature:

```sh
od -An -tx1 -j510 -N2 build/stage1.bin
```

The final command should print bytes in the order 55 aa.

## Failure triage

### Stage 1 does not appear

Check that the image is a raw disk image and that the emulator is configured
to boot it as a disk. Verify that the boot sector is exactly 512 bytes and
ends with 55 aa.

### Stage 1 reports an EDD error

The current first stage requires INT 13h Extensions. Confirm that the virtual
disk is attached through a BIOS-supported controller and that the firmware
implements EDD. The current implementation does not provide CHS fallback.

### Stage 1 reports a disk read failure

Check that the image contains the complete Stage 2 area. The DAP requests 32
sectors beginning at LBA 1. The image must therefore contain at least 33
sectors total.

### Stage 2 is not reached

Inspect the disk packet, destination address, GDT descriptor, protected-mode
far jump, and Stage 2 entry address. Confirm that the linker places
early_entry at 0x8000.

### Stage 2 faults or resets

Interrupts are disabled and there is no IDT in the current skeleton. A fault
may cause a reset or triple fault. Use QEMU's GDB stub to inspect EIP, ESP,
CR0, segment selectors, and the instruction at the faulting address.

### Stage 2 exceeds 16 KiB

Reduce the Stage 2 footprint or redesign the disk layout and Stage 1 read
count together. Do not simply remove the size check: Stage 1 currently reads
exactly 32 sectors.

### Host-side test fails

Read the failing test name and assertion. Tests should describe parser
contracts, not BIOS behavior. When changing the disk layout, update the
constants and tests together.

## Release checklist

Before creating a release candidate:

- [ ] Run the host-side unit tests.
- [ ] Build from a clean checkout.
- [ ] Confirm Stage 1 is 512 bytes.
- [ ] Confirm Stage 2 fits in 16 KiB.
- [ ] Confirm the final image is 16896 bytes.
- [ ] Inspect the boot signature.
- [ ] Run the image inspector.
- [ ] Inspect the Stage 2 ELF program headers.
- [ ] Boot the image in QEMU BIOS mode.
- [ ] Verify the visible Stage 2 output.
- [ ] Confirm documentation matches implemented behavior.
- [ ] Record unimplemented features clearly.
- [ ] Do not claim kernel boot support until an actual kernel is loaded and
  entered successfully.
