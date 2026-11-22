# SPDX-License-Identifier: GPL-2.0-or-later
"""Host-side tests for Thorn's restricted ELF32 parser."""
from __future__ import annotations

import struct
import unittest

from tools.elf32 import (
    ELFError,
    ELF_HEADER,
    PROGRAM_HEADER,
    PF_R,
    PF_X,
    PT_LOAD,
    describe_elf,
    parse_elf32,
)


def build_elf(
    *,
    magic: bytes = b"\x7fELF",
    elf_class: int = 1,
    data_encoding: int = 1,
    file_type: int = 2,
    machine: int = 3,
    entry: int = 0x100000,
    paddr: int = 0x100000,
    filesz: int = 4,
    memsz: int = 8,
    flags: int = PF_R | PF_X,
    align: int = 1,
    phoff: int = 52,
    phentsize: int = 32,
    phnum: int = 1,
    segment_offset: int = 0x100,
) -> bytes:
    ident = bytearray(16)
    ident[:4] = magic
    ident[4] = elf_class
    ident[5] = data_encoding
    ident[6] = 1
    header = ELF_HEADER.pack(
        bytes(ident), file_type, machine, 1, entry, phoff, 0, 0,
        52, phentsize, phnum, 40, 0, 0,
    )
    program = PROGRAM_HEADER.pack(
        PT_LOAD, segment_offset, paddr, paddr, filesz, memsz, flags, align
    )
    image = bytearray(max(0x200, segment_offset + filesz))
    image[:len(header)] = header
    image[phoff:phoff + len(program)] = program
    image[segment_offset:segment_offset + filesz] = b"CODE"[:filesz]
    return bytes(image)


class ELFHeaderTests(unittest.TestCase):
    def test_accepts_valid_i386_executable(self) -> None:
        image = parse_elf32(build_elf())
        self.assertEqual(image.header.machine, 3)
        self.assertEqual(image.header.entry, 0x100000)

    def test_rejects_short_header(self) -> None:
        with self.assertRaisesRegex(ELFError, "shorter"):
            parse_elf32(b"\x7fELF")

    def test_rejects_bad_magic(self) -> None:
        with self.assertRaisesRegex(ELFError, "magic"):
            parse_elf32(build_elf(magic=b"NOPE"))

    def test_rejects_elf64(self) -> None:
        with self.assertRaisesRegex(ELFError, "ELFCLASS32"):
            parse_elf32(build_elf(elf_class=2))

    def test_rejects_big_endian(self) -> None:
        with self.assertRaisesRegex(ELFError, "little-endian"):
            parse_elf32(build_elf(data_encoding=2))

    def test_rejects_shared_object(self) -> None:
        with self.assertRaisesRegex(ELFError, "executable"):
            parse_elf32(build_elf(file_type=3))

    def test_rejects_non_i386(self) -> None:
        with self.assertRaisesRegex(ELFError, "i386"):
            parse_elf32(build_elf(machine=62))

    def test_rejects_invalid_header_size(self) -> None:
        data = bytearray(build_elf())
        struct.pack_into("<H", data, 40, 10)
        with self.assertRaisesRegex(ELFError, "invalid size"):
            parse_elf32(bytes(data))


class ProgramHeaderTests(unittest.TestCase):
    def test_load_segment_is_discovered(self) -> None:
        image = parse_elf32(build_elf())
        self.assertEqual(len(image.load_segments), 1)
        self.assertEqual(image.load_segments[0].segment_type, PT_LOAD)

    def test_entry_must_be_inside_executable_segment(self) -> None:
        with self.assertRaisesRegex(ELFError, "entry point"):
            parse_elf32(build_elf(entry=0x200000))

    def test_entry_must_not_be_inside_non_executable_segment(self) -> None:
        with self.assertRaisesRegex(ELFError, "entry point"):
            parse_elf32(build_elf(flags=PF_R))

    def test_file_size_cannot_exceed_memory_size(self) -> None:
        with self.assertRaisesRegex(ELFError, "file size exceeds"):
            parse_elf32(build_elf(filesz=12, memsz=8))

    def test_segment_file_range_must_fit_file(self) -> None:
        data = build_elf(segment_offset=0x1FC, filesz=4)
        with self.assertRaisesRegex(ELFError, "out of bounds"):
            parse_elf32(data[:-1])

    def test_segment_memory_must_fit_32_bit_address_space(self) -> None:
        with self.assertRaisesRegex(ELFError, "overflow"):
            parse_elf32(build_elf(paddr=0xFFFFFFFC, entry=0xFFFFFFFC, memsz=8))

    def test_alignment_must_be_power_of_two(self) -> None:
        with self.assertRaisesRegex(ELFError, "power of two"):
            parse_elf32(build_elf(align=3))

    def test_alignment_congruence_is_checked(self) -> None:
        with self.assertRaisesRegex(ELFError, "alignment mismatch"):
            parse_elf32(build_elf(align=16, segment_offset=0x101, paddr=0x100000))

    def test_no_program_headers_is_rejected(self) -> None:
        data = bytearray(build_elf(phnum=0))
        with self.assertRaisesRegex(ELFError, "no loadable"):
            parse_elf32(bytes(data))

    def test_program_header_table_must_fit_file(self) -> None:
        data = build_elf(phoff=0x1F0)
        with self.assertRaisesRegex(ELFError, "table extends"):
            parse_elf32(data[:-16])

    def test_program_header_entry_size_must_be_large_enough(self) -> None:
        data = bytearray(build_elf(phentsize=8))
        with self.assertRaisesRegex(ELFError, "smaller"):
            parse_elf32(bytes(data))


class ReportTests(unittest.TestCase):
    def test_report_names_architecture(self) -> None:
        report = describe_elf(parse_elf32(build_elf()))
        self.assertIn("ELF32 i386 executable", report)

    def test_report_contains_entry_point(self) -> None:
        report = describe_elf(parse_elf32(build_elf()))
        self.assertIn("0x00100000", report)

    def test_report_contains_segment_permissions(self) -> None:
        report = describe_elf(parse_elf32(build_elf()))
        self.assertIn("R-X", report)

    def test_report_contains_file_size(self) -> None:
        report = describe_elf(parse_elf32(build_elf()))
        self.assertIn("File size:", report)


if __name__ == "__main__":
    unittest.main()
