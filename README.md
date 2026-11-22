# Thorn Bootloader

Thorn is an experimental x86 BIOS bootloader written in NASM and freestanding C.

## Current state

The current image contains two stages:

- **Stage 1** is a 512-byte BIOS boot sector. It selects BIOS text mode 3, checks for INT 13h Extensions (EDD), reads 32 sectors from LBA 1, enables A20, loads a GDT, and enters 32-bit protected mode.
- **Stage 2** is linked to physical address `0x8000`. Its assembly entry establishes a 16 KiB stack and calls `thorn_main()`.
- **Terminal** writes to the VGA text buffer at `0xB8000`, maintains the hardware cursor, and supports scrolling, newline, carriage return, backspace, and tabs.
- **Video** currently has a working text-mode fallback. Graphics mode is deliberately unavailable until a real-mode VBE setup path is implemented.
- **Thorn Boot Protocol (TBP)** defines the kernel handoff registers and boot-information structure. Kernel loading and handoff are not implemented yet.

The boot image is currently a development skeleton. It does not yet load or start an operating-system kernel.

## Requirements

Install the x86 build tools on a Debian or Ubuntu system:

```sh
sudo apt install gcc binutils nasm make
```

## Build

```sh
make
```

The resulting BIOS disk image is:

```text
build/boot-bios.img
```

The image consists of one 512-byte boot sector followed by a 16 KiB Stage 2 area. Stage 1 reads exactly 32 sectors beginning at LBA 1, so Stage 2 must remain at or below 16 KiB.

Clean generated files with:

```sh
make clean
```

## Test with QEMU

```sh
qemu-system-i386 -drive format=raw,file=build/boot-bios.img
```

## Thorn Boot Protocol

See [docs/boot-protocol.md](docs/boot-protocol.md) for the current register contract, flags, and boot-information structure.

## License

No license has been declared in this repository yet. All rights are reserved by default until a license is added.
