# SPDX-License-Identifier: GPL-2.0-or-later
"""Parser and builder for Thorn's raw i386 .mod file format.

The module payload is raw position-independent machine code. This module
validates and packages files on the host; it does not load or execute them.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import zlib


MOD_MAGIC = b"THRNMOD\0"
MOD_VERSION = 1
MOD_ARCH_I386 = 3
MOD_FLAG_POSITION_INDEPENDENT = 1 << 0
MOD_KNOWN_FLAGS = MOD_FLAG_POSITION_INDEPENDENT
MOD_HEADER = struct.Struct("<8sHHHHIIII")


class ModuleError(ValueError):
    """Raised for malformed or unsupported Thorn module files."""


@dataclass(frozen=True)
class ModuleImage:
    version: int
    architecture: int
    flags: int
    payload_size: int
    entry_offset: int
    payload_crc32: int
    payload: bytes
    file_size: int


def _read(source: bytes | bytearray | Path | str) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    try:
        return Path(source).read_bytes()
    except OSError as exc:
        raise ModuleError(f"cannot read module file: {exc}") from exc


def build_mod(payload: bytes | bytearray, entry_offset: int = 0) -> bytes:
    """Wrap raw i386 machine code in a version 1 Thorn module header."""
    code = bytes(payload)
    if not code:
        raise ModuleError("module payload must not be empty")
    if len(code) > 0xFFFFFFFF:
        raise ModuleError("module payload exceeds the 32-bit format limit")
    if not 0 <= entry_offset < len(code):
        raise ModuleError("entry offset is outside the module payload")

    checksum = zlib.crc32(code) & 0xFFFFFFFF
    header = MOD_HEADER.pack(
        MOD_MAGIC,
        MOD_VERSION,
        MOD_HEADER.size,
        MOD_ARCH_I386,
        MOD_FLAG_POSITION_INDEPENDENT,
        len(code),
        entry_offset,
        checksum,
        0,
    )
    return header + code


def parse_mod(source: bytes | bytearray | Path | str) -> ModuleImage:
    """Parse a .mod file and validate its header, bounds, and payload CRC."""
    data = _read(source)
    if len(data) < MOD_HEADER.size:
        raise ModuleError("file is shorter than the Thorn module header")

    (
        magic,
        version,
        header_size,
        architecture,
        flags,
        payload_size,
        entry_offset,
        payload_crc32,
        reserved,
    ) = MOD_HEADER.unpack_from(data)

    if magic != MOD_MAGIC:
        raise ModuleError("invalid Thorn module magic")
    if version != MOD_VERSION:
        raise ModuleError(f"unsupported Thorn module version: {version}")
    if header_size != MOD_HEADER.size:
        raise ModuleError("invalid Thorn module header size")
    if architecture != MOD_ARCH_I386:
        raise ModuleError("module architecture is not i386")
    if flags & ~MOD_KNOWN_FLAGS:
        raise ModuleError("module contains unknown flag bits")
    if not flags & MOD_FLAG_POSITION_INDEPENDENT:
        raise ModuleError("module payload is not marked position-independent")
    if reserved != 0:
        raise ModuleError("reserved header field must be zero")
    if payload_size == 0:
        raise ModuleError("module payload must not be empty")
    if len(data) != header_size + payload_size:
        raise ModuleError("module payload size does not match file size")
    if entry_offset >= payload_size:
        raise ModuleError("entry offset is outside the module payload")

    payload = data[header_size:]
    actual_crc32 = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_crc32 != payload_crc32:
        raise ModuleError("module payload CRC-32 mismatch")

    return ModuleImage(
        version=version,
        architecture=architecture,
        flags=flags,
        payload_size=payload_size,
        entry_offset=entry_offset,
        payload_crc32=payload_crc32,
        payload=payload,
        file_size=len(data),
    )


def describe_mod(module: ModuleImage) -> str:
    """Format a concise human-readable module report."""
    return "\n".join(
        (
            "Thorn raw module",
            f"Format version: {module.version}",
            "Architecture: i386",
            "Payload: position-independent raw machine code",
            f"File size: {module.file_size} bytes",
            f"Payload size: {module.payload_size} bytes",
            f"Entry offset: 0x{module.entry_offset:08x}",
            f"Payload CRC-32: 0x{module.payload_crc32:08x}",
        )
    )
