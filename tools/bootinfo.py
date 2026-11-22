# SPDX-License-Identifier: GPL-2.0-or-later
"""Host-side reader and validator for the Thorn Boot Protocol structure."""
from __future__ import annotations

from dataclasses import dataclass
import struct


TBP_MAGIC = 0x5448524E
FLAG_MEMORY_MAP = 1 << 0
FLAG_BOOT_DRIVE = 1 << 1
FLAG_FRAMEBUFFER = 1 << 2
FLAG_KERNEL = 1 << 3
KNOWN_FLAGS = FLAG_MEMORY_MAP | FLAG_BOOT_DRIVE | FLAG_FRAMEBUFFER | FLAG_KERNEL
BOOT_INFO = struct.Struct("<10I")


class BootInfoError(ValueError):
    """Raised when a serialized TBP structure is malformed."""


@dataclass(frozen=True)
class BootInfo:
    boot_drive: int
    memory_map_address: int
    memory_map_entries: int
    kernel_address: int
    kernel_size: int
    framebuffer_address: int
    framebuffer_width: int
    framebuffer_height: int
    framebuffer_pitch: int
    framebuffer_bpp: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "BootInfo":
        if len(data) < BOOT_INFO.size:
            raise BootInfoError(
                f"boot information is truncated ({len(data)} < {BOOT_INFO.size})"
            )
        return cls(*BOOT_INFO.unpack_from(data))

    def to_bytes(self) -> bytes:
        values = tuple(self.__dict__.values())
        return BOOT_INFO.pack(*values)


@dataclass(frozen=True)
class BootContext:
    magic: int
    flags: int
    info: BootInfo


def validate_context(context: BootContext) -> None:
    """Check magic, known flags, and consistency of advertised capabilities."""
    if context.magic != TBP_MAGIC:
        raise BootInfoError("invalid TBP magic")
    if context.flags & ~KNOWN_FLAGS:
        raise BootInfoError("unknown TBP flag bits are set")

    info = context.info
    if context.flags & FLAG_MEMORY_MAP:
        if info.memory_map_address == 0 or info.memory_map_entries == 0:
            raise BootInfoError("memory-map flag set without a populated map")
    elif info.memory_map_address or info.memory_map_entries:
        raise BootInfoError("memory-map fields populated while flag is clear")

    if context.flags & FLAG_BOOT_DRIVE:
        if info.boot_drive == 0:
            raise BootInfoError("boot-drive flag set with an empty drive value")
    elif info.boot_drive:
        raise BootInfoError("boot-drive field populated while flag is clear")

    if context.flags & FLAG_FRAMEBUFFER:
        if not all((
            info.framebuffer_address,
            info.framebuffer_width,
            info.framebuffer_height,
            info.framebuffer_pitch,
            info.framebuffer_bpp,
        )):
            raise BootInfoError("framebuffer flag set with incomplete metadata")
        minimum_pitch = info.framebuffer_width * ((info.framebuffer_bpp + 7) // 8)
        if info.framebuffer_pitch < minimum_pitch:
            raise BootInfoError("framebuffer pitch is smaller than one visible row")
    elif any((
        info.framebuffer_address,
        info.framebuffer_width,
        info.framebuffer_height,
        info.framebuffer_pitch,
        info.framebuffer_bpp,
    )):
        raise BootInfoError("framebuffer fields populated while flag is clear")

    if context.flags & FLAG_KERNEL:
        if info.kernel_address == 0 or info.kernel_size == 0:
            raise BootInfoError("kernel flag set without a loaded kernel")
    elif info.kernel_address or info.kernel_size:
        raise BootInfoError("kernel fields populated while flag is clear")


def parse_context(magic: int, flags: int, data: bytes) -> BootContext:
    """Decode and validate a register tuple plus serialized boot information."""
    context = BootContext(magic, flags, BootInfo.from_bytes(data))
    validate_context(context)
    return context


def describe_context(context: BootContext) -> str:
    """Return a stable human-readable TBP summary."""
    names = (
        (FLAG_MEMORY_MAP, "memory-map"),
        (FLAG_BOOT_DRIVE, "boot-drive"),
        (FLAG_FRAMEBUFFER, "framebuffer"),
        (FLAG_KERNEL, "kernel"),
    )
    enabled = [name for bit, name in names if context.flags & bit]
    lines = [
        f"TBP magic: 0x{context.magic:08x}",
        f"Flags: 0x{context.flags:08x}",
        "Capabilities: " + (", ".join(enabled) if enabled else "none"),
        f"Boot drive: 0x{context.info.boot_drive:02x}",
        f"Memory map: 0x{context.info.memory_map_address:08x} "
        f"({context.info.memory_map_entries} entries)",
        f"Kernel: 0x{context.info.kernel_address:08x} "
        f"({context.info.kernel_size} bytes)",
        f"Framebuffer: 0x{context.info.framebuffer_address:08x} "
        f"{context.info.framebuffer_width}x{context.info.framebuffer_height} "
        f"{context.info.framebuffer_bpp} bpp, pitch "
        f"{context.info.framebuffer_pitch}",
    ]
    return "\n".join(lines)
