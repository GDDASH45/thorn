# SPDX-License-Identifier: GPL-2.0-or-later
"""Small, defensive ELF32 reader for host-side Thorn image analysis.

The parser is deliberately limited to ELF32 little-endian i386 executables.
It does not load files into memory or execute any input.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct


ELF_MAGIC = b"\x7fELF"
ELFCLASS32 = 1
ELFDATA2LSB = 1
EV_CURRENT = 1
ET_EXEC = 2
EM_386 = 3
PT_LOAD = 1
PF_X = 1
PF_W = 2
PF_R = 4
ELF_HEADER = struct.Struct("<16sHHIIIIIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIIIIIII")


class ELFError(ValueError):
    """Raised for malformed or unsupported ELF input."""


@dataclass(frozen=True)
class ELFHeader:
    file_type: int
    machine: int
    version: int
    entry: int
    program_offset: int
    section_offset: int
    flags: int
    header_size: int
    program_entry_size: int
    program_count: int
    section_entry_size: int
    section_count: int
    section_name_index: int


@dataclass(frozen=True)
class ProgramHeader:
    index: int
    segment_type: int
    offset: int
    virtual_address: int
    physical_address: int
    file_size: int
    memory_size: int
    flags: int
    alignment: int

    @property
    def file_end(self) -> int:
        return self.offset + self.file_size

    @property
    def memory_end(self) -> int:
        return self.physical_address + self.memory_size

    @property
    def is_loadable(self) -> bool:
        return self.segment_type == PT_LOAD

    @property
    def executable(self) -> bool:
        return bool(self.flags & PF_X)

    @property
    def writable(self) -> bool:
        return bool(self.flags & PF_W)

    @property
    def readable(self) -> bool:
        return bool(self.flags & PF_R)


@dataclass(frozen=True)
class ELFImage:
    header: ELFHeader
    program_headers: tuple[ProgramHeader, ...]
    file_size: int

    @property
    def load_segments(self) -> tuple[ProgramHeader, ...]:
        return tuple(p for p in self.program_headers if p.is_loadable)

    @property
    def entry_segment(self) -> ProgramHeader | None:
        for segment in self.load_segments:
            if (
                segment.executable
                and segment.physical_address <= self.header.entry
                < segment.memory_end
            ):
                return segment
        return None


def _read(source: bytes | bytearray | Path | str) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    try:
        return Path(source).read_bytes()
    except OSError as exc:
        raise ELFError(f"cannot read ELF file: {exc}") from exc


def _decode_header(data: bytes) -> ELFHeader:
    if len(data) < ELF_HEADER.size:
        raise ELFError("file is shorter than the ELF32 header")
    fields = ELF_HEADER.unpack_from(data)
    ident = fields[0]
    if ident[:4] != ELF_MAGIC:
        raise ELFError("invalid ELF magic")
    if ident[4] != ELFCLASS32:
        raise ELFError("only ELFCLASS32 is supported")
    if ident[5] != ELFDATA2LSB:
        raise ELFError("only little-endian ELF is supported")
    if ident[6] != EV_CURRENT:
        raise ELFError("unsupported ELF identification version")

    return ELFHeader(
        file_type=fields[1],
        machine=fields[2],
        version=fields[3],
        entry=fields[4],
        program_offset=fields[5],
        section_offset=fields[6],
        flags=fields[7],
        header_size=fields[8],
        program_entry_size=fields[9],
        program_count=fields[10],
        section_entry_size=fields[11],
        section_count=fields[12],
        section_name_index=fields[13],
    )


def _decode_program_headers(data: bytes, header: ELFHeader) -> tuple[ProgramHeader, ...]:
    if header.program_count == 0:
        return ()
    if header.program_entry_size < PROGRAM_HEADER.size:
        raise ELFError("program-header entries are smaller than ELF32 minimum")
    table_end = header.program_offset + header.program_entry_size * header.program_count
    if table_end > len(data):
        raise ELFError("program-header table extends beyond end of file")

    result: list[ProgramHeader] = []
    for index in range(header.program_count):
        offset = header.program_offset + index * header.program_entry_size
        values = PROGRAM_HEADER.unpack_from(data, offset)
        result.append(
            ProgramHeader(
                index=index,
                segment_type=values[0],
                offset=values[1],
                virtual_address=values[2],
                physical_address=values[3],
                file_size=values[4],
                memory_size=values[5],
                flags=values[6],
                alignment=values[7],
            )
        )
    return tuple(result)


def parse_elf32(source: bytes | bytearray | Path | str) -> ELFImage:
    """Parse an ELF32 file and perform structural bounds checks."""
    data = _read(source)
    header = _decode_header(data)
    if header.header_size < ELF_HEADER.size:
        raise ELFError("ELF header reports an invalid size")
    if header.header_size > len(data):
        raise ELFError("ELF header size extends beyond file")
    if header.file_type != ET_EXEC:
        raise ELFError("input is not an executable ELF file")
    if header.machine != EM_386:
        raise ELFError("input is not an i386 executable")
    if header.version != EV_CURRENT:
        raise ELFError("unsupported ELF version")

    programs = _decode_program_headers(data, header)
    image = ELFImage(header, programs, len(data))
    validate_load_segments(image)
    return image


def validate_load_segments(image: ELFImage) -> None:
    """Validate PT_LOAD file ranges and basic segment invariants."""
    for segment in image.load_segments:
        if segment.file_size > segment.memory_size:
            raise ELFError(f"PT_LOAD {segment.index}: file size exceeds memory size")
        if segment.file_end > image.file_size:
            raise ELFError(f"PT_LOAD {segment.index}: file data is out of bounds")
        if segment.memory_end > 0x1_0000_0000:
            raise ELFError(f"PT_LOAD {segment.index}: 32-bit address overflow")
        if segment.alignment not in (0, 1):
            if segment.alignment & (segment.alignment - 1):
                raise ELFError(f"PT_LOAD {segment.index}: alignment is not a power of two")
            if (segment.virtual_address - segment.offset) % segment.alignment:
                raise ELFError(f"PT_LOAD {segment.index}: address/offset alignment mismatch")
    if not image.load_segments:
        raise ELFError("ELF file has no loadable segments")
    if image.entry_segment is None:
        raise ELFError("entry point is not inside an executable PT_LOAD segment")


def describe_elf(image: ELFImage) -> str:
    """Format a compact report suitable for command-line diagnostics."""
    h = image.header
    lines = [
        "ELF32 i386 executable",
        f"File size: {image.file_size} bytes",
        f"Entry point: 0x{h.entry:08x}",
        f"Program headers: {len(image.program_headers)}",
        f"Loadable segments: {len(image.load_segments)}",
    ]
    for segment in image.load_segments:
        flags = "".join(
            letter if enabled else "-"
            for letter, enabled in (
                ("R", segment.readable),
                ("W", segment.writable),
                ("X", segment.executable),
            )
        )
        lines.append(
            f"  [{segment.index}] {flags} "
            f"paddr=0x{segment.physical_address:08x} "
            f"filesz=0x{segment.file_size:x} "
            f"memsz=0x{segment.memory_size:x} "
            f"align=0x{segment.alignment:x}"
        )
    return "\n".join(lines)
