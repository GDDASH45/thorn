# Thorn Bootloader

Thorn is an experimental x86 BIOS bootloader written in NASM and freestanding C.
It is designed as a small, inspectable boot path rather than a feature-complete
operating-system loader.

## Current implementation

The current image contains two stages:

- **Stage 1** is a 512-byte BIOS boot sector. It selects BIOS text mode 3,
  checks for INT 13h Extensions (EDD), reads 32 sectors from LBA 1, enables
  A20, loads a GDT, and enters 32-bit protected mode.
- **Stage 2** is linked to physical address 0x8000. Its assembly entry
  establishes a 16 KiB stack and calls thorn_main().
- **Terminal** writes to the VGA text buffer at 0xB8000, maintains the
  hardware cursor, and supports scrolling, newline, carriage return,
  backspace, and tabs.
- **Video** currently has a text-mode fallback. Graphics mode is deliberately
  unavailable until a real-mode VBE setup path is implemented.
- **Thorn Boot Protocol (TBP)** defines the kernel handoff registers and
  boot-information structure. The handoff routine exists, but kernel loading
  and invocation are not implemented.

The boot image is a development skeleton. It does not yet load or start an
operating-system kernel. See docs/architecture.md for the stage-by-stage design
and implementation boundaries.

## Requirements

Install the x86 build tools on a Debian or Ubuntu system:

~~~sh
sudo apt install gcc binutils nasm make python3
~~~

QEMU is optional and is only needed for emulator testing.

## Build

~~~sh
make
~~~

The resulting BIOS disk image is build/boot-bios.img.

The image consists of one 512-byte boot sector followed by a 16 KiB Stage 2
area. Stage 1 reads exactly 32 sectors beginning at LBA 1, so Stage 2 must
remain at or below 16 KiB.

Clean generated files with:

~~~sh
make clean
~~~

## Host-side tests

Run the Python standard-library test suite:

~~~sh
make test
~~~

The tests cover image-layout checks, ELF32 structural validation, TBP
metadata consistency, and the raw .mod file format. They do not emulate BIOS
behavior.

## Inspection tools

Inspect the raw BIOS image:

~~~sh
python3 tools/inspect-image.py build/boot-bios.img
~~~

Emit JSON for scripts:

~~~sh
python3 tools/inspect-image.py --json build/boot-bios.img
~~~

Inspect the linked ELF32 file:

~~~sh
python3 tools/inspect-elf.py build/stage2.elf
~~~

The inspection utilities are host-side tools. The current BIOS loader reads a
flat binary, not an ELF file.

## Raw module files

Thorn defines a versioned .mod container for position-independent raw i386
machine code. The host-side packer and inspector are documented in
docs/module-format.md:

~~~sh
python3 tools/pack-mod.py module.bin module.mod --entry-offset 0
python3 tools/inspect-mod.py module.mod
~~~

The module execution ABI is documented in docs/module-abi.md. The TBP command
module can be built with:

~~~sh
make modules
~~~

This produces build/tbp.mod. Its intended boot-script syntax is:

~~~sh
tbp /boot/kernel.bin --verbose
~~~

The module ABI defines the loader and handoff service calls, including
forwarding arguments after the kernel path to the TBP command-line handoff.
The current boot path does not yet implement module execution, filesystem
access, kernel loading, or the boot-script interpreter.

## Test with QEMU

~~~sh
qemu-system-i386 -drive format=raw,file=build/boot-bios.img
~~~

The expected current behavior is to print the Stage 2 status messages and
halt. Kernel loading is not implemented yet.

## Documentation

- Architecture and execution flow: docs/architecture.md
- Disk and memory layout: docs/disk-layout.md
- Thorn Boot Protocol: docs/boot-protocol.md
- Module execution ABI: docs/module-abi.md
- ELF32 inspection utility: docs/elf32-tool.md
- Raw .mod module format: docs/module-format.md
- TBP metadata validation: docs/bootinfo-validation.md
- Testing and debugging: docs/testing.md
- Contribution guidelines: docs/contributing.md
- Roadmap: docs/roadmap.md

## License

Thorn is licensed under the GNU General Public License, version 2 or (at your
option) any later version. See LICENSE.

SPDX-License-Identifier: GPL-2.0-or-later
