# SPDX-License-Identifier: GPL-2.0-or-later
"""Host-side tests for Thorn's raw .mod file format."""
from __future__ import annotations

import struct
import unittest
import zlib

from tools.modfile import (
    MOD_ARCH_I386,
    MOD_FLAG_POSITION_INDEPENDENT,
    MOD_HEADER,
    MOD_MAGIC,
    MOD_VERSION,
    ModuleError,
    build_mod,
    describe_mod,
    parse_mod,
)


class ModuleFormatTests(unittest.TestCase):
    def test_build_and_parse_round_trip(self) -> None:
        payload = b"\x90\x90\xC3"
        module = parse_mod(build_mod(payload))
        self.assertEqual(module.payload, payload)
        self.assertEqual(module.payload_size, len(payload))
        self.assertEqual(module.entry_offset, 0)

    def test_entry_offset_is_preserved(self) -> None:
        module = parse_mod(build_mod(b"\x90\x90\xC3", entry_offset=2))
        self.assertEqual(module.entry_offset, 2)

    def test_header_is_32_bytes(self) -> None:
        self.assertEqual(MOD_HEADER.size, 32)
        self.assertEqual(len(build_mod(b"\xC3")[:32]), 32)

    def test_format_identifies_i386_and_pic(self) -> None:
        module = parse_mod(build_mod(b"\xC3"))
        self.assertEqual(module.architecture, MOD_ARCH_I386)
        self.assertEqual(module.flags, MOD_FLAG_POSITION_INDEPENDENT)

    def test_rejects_short_header(self) -> None:
        with self.assertRaisesRegex(ModuleError, "shorter"):
            parse_mod(b"THRNMOD")

    def test_rejects_bad_magic(self) -> None:
        data = bytearray(build_mod(b"\xC3"))
        data[0:8] = b"BADMOD!!"
        with self.assertRaisesRegex(ModuleError, "magic"):
            parse_mod(data)

    def test_rejects_unsupported_version(self) -> None:
        data = bytearray(build_mod(b"\xC3"))
        struct.pack_into("<H", data, 8, MOD_VERSION + 1)
        with self.assertRaisesRegex(ModuleError, "version"):
            parse_mod(data)

    def test_rejects_wrong_header_size(self) -> None:
        data = bytearray(build_mod(b"\xC3"))
        struct.pack_into("<H", data, 10, 31)
        with self.assertRaisesRegex(ModuleError, "header size"):
            parse_mod(data)

    def test_rejects_wrong_architecture(self) -> None:
        data = bytearray(build_mod(b"\xC3"))
        struct.pack_into("<H", data, 12, 62)
        with self.assertRaisesRegex(ModuleError, "i386"):
            parse_mod(data)

    def test_rejects_missing_pic_flag(self) -> None:
        data = bytearray(build_mod(b"\xC3"))
        struct.pack_into("<H", data, 14, 0)
        with self.assertRaisesRegex(ModuleError, "position-independent"):
            parse_mod(data)

    def test_rejects_unknown_flags(self) -> None:
        data = bytearray(build_mod(b"\xC3"))
        struct.pack_into("<H", data, 14, MOD_FLAG_POSITION_INDEPENDENT | 2)
        with self.assertRaisesRegex(ModuleError, "unknown flag"):
            parse_mod(data)

    def test_rejects_empty_payload(self) -> None:
        with self.assertRaisesRegex(ModuleError, "must not be empty"):
            build_mod(b"")

    def test_rejects_payload_size_mismatch(self) -> None:
        data = bytearray(build_mod(b"\x90\xC3"))
        struct.pack_into("<I", data, 16, 3)
        with self.assertRaisesRegex(ModuleError, "does not match"):
            parse_mod(data)

    def test_rejects_trailing_bytes(self) -> None:
        with self.assertRaisesRegex(ModuleError, "does not match"):
            parse_mod(build_mod(b"\xC3") + b"extra")

    def test_rejects_entry_outside_payload(self) -> None:
        data = bytearray(build_mod(b"\xC3"))
        struct.pack_into("<I", data, 20, 1)
        with self.assertRaisesRegex(ModuleError, "entry offset"):
            parse_mod(data)

    def test_rejects_reserved_field(self) -> None:
        data = bytearray(build_mod(b"\xC3"))
        struct.pack_into("<I", data, 28, 1)
        with self.assertRaisesRegex(ModuleError, "reserved"):
            parse_mod(data)

    def test_rejects_payload_crc_mismatch(self) -> None:
        data = bytearray(build_mod(b"\x90\xC3"))
        data[-1] ^= 0xFF
        with self.assertRaisesRegex(ModuleError, "CRC-32"):
            parse_mod(data)

    def test_report_contains_module_details(self) -> None:
        report = describe_mod(parse_mod(build_mod(b"\xC3")))
        self.assertIn("Thorn raw module", report)
        self.assertIn("Architecture: i386", report)
        self.assertIn("Entry offset:", report)


if __name__ == "__main__":
    unittest.main()
