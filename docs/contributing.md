# Contributing to Thorn

Contributions should keep the boot path small, explicit, and testable. The
project is experimental, so accurate implementation status is more important
than a long feature list.

## Before changing code

Read the architecture document and identify which execution stage owns the
behavior being changed.

Stage 1 runs in 16-bit real mode and can use BIOS services. Stage 2 runs in
32-bit protected mode and cannot call real-mode BIOS services directly.

A change that crosses this boundary needs an explicit transition design. Do
not add an INT 10h or INT 13h call to ordinary Stage 2 C code and assume it
will work.

## Keep the disk contract synchronized

The current first stage reads exactly 32 sectors beginning at LBA 1. The
Stage 2 binary is limited to 16 KiB and the final raw image is 16896 bytes.

Any disk-layout change must update the assembly, Makefile, host-side tools,
tests, and documentation together.

## C and assembly

C code is freestanding and targets 32-bit x86. Do not introduce hosted
runtime assumptions or libc dependencies without deliberately adding and
linking the required runtime support.

Assembly entry points must document register contracts and stack ownership.
If an assembly routine calls C, establish a valid stack and follow the
compiler's calling convention.

The kernel handoff is a register-based protocol. A kernel's first assembly
stub should capture EAX, EBX, and ECX before calling ordinary C code.

## Error handling

Reject malformed input before using it. Validate all lengths and offsets
before reading, copying, or jumping to data supplied by a disk image.

Avoid silent fallback when a required operation has failed. A fallback is
appropriate only when the alternative behavior is defined and the resulting
capabilities are reported accurately.

## Tests

Add host-side tests for parsers and deterministic helper functions. Tests
should not require root privileges, physical disks, or a network connection.

Run:

```sh
make test
```

When changing the boot image, also run:

```sh
make clean
make
python3 tools/inspect-image.py build/boot-bios.img
```

Emulator testing is still required for changes that affect real-mode startup,
disk access, protected-mode transition, video, or Stage 2 execution.

## Documentation

Update the documentation when changing:

- The stage transition sequence.
- The raw disk layout.
- Physical memory ownership.
- The boot protocol.
- Supported architectures or firmware.
- Build dependencies.
- The set of implemented capabilities.

Clearly label planned features. Do not describe a declaration, stub, or
roadmap item as a completed implementation.

## Commit messages

Use concise, action-oriented commit subjects. Suggested prefixes include:

- `stage1:` for BIOS boot-sector work.
- `stage2:` for protected-mode initialization.
- `terminal:` for text output.
- `video:` for display initialization.
- `tbp:` for boot protocol changes.
- `tools:` for host utilities.
- `tests:` for tests.
- `docs:` for documentation.
- `build:` for Makefile and build changes.
- `license:` for licensing changes.

Keep unrelated changes in separate commits so they can be reviewed and
reverted independently.

## Licensing

Thorn is distributed under GNU GPL version 2 or, at your option, any later
version. New contributions to the project must be compatible with that
license.

Add an SPDX identifier to new source files:

`SPDX-License-Identifier: GPL-2.0-or-later`

Do not copy code from projects with incompatible licensing terms. If a
contribution includes third-party code, preserve its notices and document
its license.

## Review checklist

Before asking for review:

- [ ] The change has a clear purpose.
- [ ] The correct stage owns the new behavior.
- [ ] BIOS-only operations remain in a BIOS-capable execution context.
- [ ] Disk and memory bounds are checked.
- [ ] The compiler and assembler accept the code.
- [ ] The Stage 2 size limit is preserved.
- [ ] Host-side tests pass.
- [ ] Emulator tests are performed when relevant.
- [ ] Documentation matches the implementation.
- [ ] No generated build artifacts are committed.
- [ ] New files carry the project SPDX identifier.
