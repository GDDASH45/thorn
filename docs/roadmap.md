# Thorn roadmap

This roadmap separates the current boot skeleton from possible future work.
Items listed here are not implemented unless the current-state documentation
also says they are implemented.

## Current baseline

The current baseline includes:

- A 512-byte BIOS boot sector.
- EDD presence checking.
- A fixed 32-sector Stage 2 read.
- A20 enable through port 0x92.
- A flat 32-bit GDT.
- A protected-mode transition.
- A Stage 2 entry stub and stack.
- VGA text output and cursor handling.
- A text-mode fallback.
- A documented register-based TBP.
- Host-side image, ELF32, and boot-information inspection tools.
- Unit tests for the host-side validation tools.

The baseline does not load an operating-system kernel.

## Stage A: make the current path observable

Possible work:

- Add a compact Stage 1 status code path.
- Preserve BIOS disk error codes for diagnostics.
- Add a serial output backend for QEMU debugging.
- Add a stable Stage 2 diagnostic banner.
- Add linker assertions for entry placement and memory boundaries.
- Add an automated clean build check.
- Record emulator test instructions for BIOS disk variants.

Acceptance conditions:

- The boot sector remains exactly 512 bytes.
- The Stage 2 image remains within its allocated sectors.
- The diagnostic path does not invoke BIOS services after protected-mode entry.
- Failure paths halt rather than continuing with uncertain state.

## Stage B: establish protected-mode fault handling

Possible work:

- Define an IDT.
- Install exception handlers for processor exceptions.
- Add a dedicated double-fault path.
- Add a minimal GDT/TSS policy if required.
- Define stack ownership for exceptions.
- Print exception vectors and error codes through a safe output backend.

Acceptance conditions:

- The IDT is initialized before interrupts are enabled.
- Exception handlers do not depend on uninitialized video or memory state.
- A deliberate test fault produces a diagnostic rather than an unexplained reset.
- Interrupt state is restored only when the required handlers are ready.

## Stage C: memory discovery

Possible work:

- Add an E820 memory-map collection path while BIOS calls are available.
- Validate returned continuation values.
- Handle variable-size E820 entries.
- Preserve enabled and disabled entries accurately.
- Store a bounded memory map in a documented physical buffer.
- Define a stable memory-map entry structure for TBP.

Acceptance conditions:

- BIOS calls are made in real mode or through a tested thunk.
- Entry counts are bounded.
- Arithmetic is checked for overflow.
- The buffer cannot overlap Stage 1, Stage 2, stack, or kernel destination.
- The memory-map capability flag is set only after the map is complete.

## Stage D: video initialization

Possible work:

- Query VBE controller information.
- Enumerate supported modes.
- Query a selected mode's attributes and framebuffer layout.
- Validate width, height, pitch, and bits per pixel.
- Set the mode before leaving the BIOS-capable environment.
- Preserve framebuffer metadata for the kernel.
- Add a simple framebuffer console only after mode setup works.

Acceptance conditions:

- A successful mode-set result is checked.
- Returned framebuffer information is validated.
- The framebuffer capability flag is set only when all required fields are valid.
- Text fallback remains available when no suitable mode exists.
- The kernel does not need to switch modes to inherit the selected mode.

## Stage E: disk abstraction

Possible work:

- Define a small disk-read interface.
- Preserve the BIOS drive number.
- Add bounded retry behavior for transient BIOS errors.
- Split requests to satisfy BIOS transfer limits.
- Validate destination ranges.
- Keep the Stage 1 boot sector within 512 bytes.

Acceptance conditions:

- Failed reads return an explicit error.
- Sector arithmetic cannot overflow.
- No read writes outside the destination buffer.
- BIOS drive identity survives the stage transition.
- The fixed disk image contract is documented.

## Stage F: kernel image format

Possible work:

- Define a kernel file selection policy.
- Add a documented ELF32 loading profile.
- Validate ELF headers and every loadable segment.
- Reject unsupported dynamic and relocation features.
- Reserve destination memory before copying.
- Zero the memory tail of each segment.
- Verify that the entry point belongs to an executable loaded segment.

Acceptance conditions:

- The loader never jumps to an unvalidated address.
- All file ranges fit the source image.
- All physical ranges fit usable memory.
- Segment overlaps are handled by a documented policy.
- Kernel metadata is populated only after the full image is loaded.
- The kernel capability flag is set only after success.

## Stage G: real-mode services boundary

VBE and E820 require BIOS services. Possible designs include:

- Perform all required BIOS discovery before entering protected mode.
- Return to real mode through a carefully specified transition.
- Implement a dedicated real-mode thunk with protected-mode state save and
  restore.

A thunk is not merely an INT instruction. It must manage CPU mode transitions,
descriptor tables, stack state, A20 state, and firmware assumptions. It needs
dedicated tests.

The project should choose one design before adding scattered BIOS calls to
Stage 2.

## Stage H: final kernel handoff

Possible work:

- Finalize the boot-information layout.
- Ensure the structure remains in memory after handoff.
- Define stack and interrupt-state requirements for kernel entry.
- Load the kernel entry address only after successful image validation.
- Populate the register contract.
- Transfer control through the assembly handoff routine.

Acceptance conditions:

- EAX contains the documented magic.
- EBX contains only valid capability flags.
- ECX points to a valid boot-information structure.
- The kernel entry address is inside a loaded executable range.
- The bootloader does not execute code after a successful handoff.

## Stage I: compatibility and release

Possible work:

- Test multiple QEMU machine types.
- Test BIOS disk controller variations.
- Test with different virtual disk sizes.
- Document firmware limitations.
- Add reproducible release artifacts.
- Add a release checklist and versioning policy.

Acceptance conditions:

- Clean build and host tests pass.
- Boot smoke tests are reproducible.
- Release notes list tested and untested configurations.
- The project does not claim UEFI or kernel-loading support prematurely.

## Explicitly deferred

The following are not part of the current baseline:

- UEFI application support.
- 64-bit long-mode transition.
- Secure Boot.
- Cryptographic kernel authentication.
- Filesystem support.
- Network boot.
- SMP startup.
- ACPI parsing.
- Device-tree support.
- Chainloading another bootloader.

These may be considered after the BIOS path and kernel handoff are stable.
