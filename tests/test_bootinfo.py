"""Tests for Thorn Boot Protocol metadata validation."""
from __future__ import annotations

import unittest

from tools.bootinfo import (
    BOOT_INFO,
    FLAG_BOOT_DRIVE,
    FLAG_FRAMEBUFFER,
    FLAG_KERNEL,
    FLAG_MEMORY_MAP,
    TBP_MAGIC,
    BootContext,
    BootInfo,
    BootInfoError,
    describe_context,
    parse_context,
    validate_context,
)


def blank_info(**updates: int) -> BootInfo:
    fields = {
        "boot_drive": 0,
        "memory_map_address": 0,
        "memory_map_entries": 0,
        "kernel_address": 0,
        "kernel_size": 0,
        "framebuffer_address": 0,
        "framebuffer_width": 0,
        "framebuffer_height": 0,
        "framebuffer_pitch": 0,
        "framebuffer_bpp": 0,
    }
    fields.update(updates)
    return BootInfo(**fields)


class StructureTests(unittest.TestCase):
    def test_structure_size_is_forty_bytes(self) -> None:
        self.assertEqual(BOOT_INFO.size, 40)

    def test_round_trip(self) -> None:
        original = blank_info(boot_drive=0x80)
        self.assertEqual(BootInfo.from_bytes(original.to_bytes()), original)

    def test_truncated_structure_is_rejected(self) -> None:
        with self.assertRaisesRegex(BootInfoError, "truncated"):
            BootInfo.from_bytes(b"\x00" * 39)

    def test_extra_bytes_are_ignored_by_decoder(self) -> None:
        original = blank_info()
        decoded = BootInfo.from_bytes(original.to_bytes() + b"extra")
        self.assertEqual(decoded, original)


class ContextTests(unittest.TestCase):
    def test_empty_context_is_valid(self) -> None:
        validate_context(BootContext(TBP_MAGIC, 0, blank_info()))

    def test_wrong_magic_is_rejected(self) -> None:
        with self.assertRaisesRegex(BootInfoError, "magic"):
            validate_context(BootContext(0, 0, blank_info()))

    def test_unknown_flags_are_rejected(self) -> None:
        with self.assertRaisesRegex(BootInfoError, "unknown"):
            validate_context(BootContext(TBP_MAGIC, 0x80000000, blank_info()))

    def test_memory_map_flag_requires_data(self) -> None:
        info = blank_info(memory_map_address=0x5000, memory_map_entries=2)
        validate_context(BootContext(TBP_MAGIC, FLAG_MEMORY_MAP, info))

    def test_memory_map_flag_rejects_missing_address(self) -> None:
        info = blank_info(memory_map_entries=2)
        with self.assertRaisesRegex(BootInfoError, "memory-map flag"):
            validate_context(BootContext(TBP_MAGIC, FLAG_MEMORY_MAP, info))

    def test_memory_map_fields_must_be_zero_without_flag(self) -> None:
        info = blank_info(memory_map_address=0x5000, memory_map_entries=2)
        with self.assertRaisesRegex(BootInfoError, "flag is clear"):
            validate_context(BootContext(TBP_MAGIC, 0, info))

    def test_boot_drive_flag_requires_nonzero_drive(self) -> None:
        validate_context(BootContext(TBP_MAGIC, FLAG_BOOT_DRIVE, blank_info(boot_drive=0x80)))

    def test_boot_drive_without_value_is_rejected(self) -> None:
        with self.assertRaisesRegex(BootInfoError, "boot-drive flag"):
            validate_context(BootContext(TBP_MAGIC, FLAG_BOOT_DRIVE, blank_info()))

    def test_framebuffer_requires_complete_metadata(self) -> None:
        info = blank_info(
            framebuffer_address=0xE0000000,
            framebuffer_width=800,
            framebuffer_height=600,
            framebuffer_pitch=3200,
            framebuffer_bpp=32,
        )
        validate_context(BootContext(TBP_MAGIC, FLAG_FRAMEBUFFER, info))

    def test_framebuffer_rejects_short_pitch(self) -> None:
        info = blank_info(
            framebuffer_address=0xE0000000,
            framebuffer_width=800,
            framebuffer_height=600,
            framebuffer_pitch=100,
            framebuffer_bpp=32,
        )
        with self.assertRaisesRegex(BootInfoError, "pitch"):
            validate_context(BootContext(TBP_MAGIC, FLAG_FRAMEBUFFER, info))

    def test_kernel_flag_requires_loaded_image(self) -> None:
        info = blank_info(kernel_address=0x100000, kernel_size=4096)
        validate_context(BootContext(TBP_MAGIC, FLAG_KERNEL, info))

    def test_kernel_flag_rejects_empty_image(self) -> None:
        with self.assertRaisesRegex(BootInfoError, "kernel flag"):
            validate_context(BootContext(TBP_MAGIC, FLAG_KERNEL, blank_info()))

    def test_all_known_flags_can_coexist(self) -> None:
        info = blank_info(
            boot_drive=0x80,
            memory_map_address=0x5000,
            memory_map_entries=1,
            kernel_address=0x100000,
            kernel_size=4096,
            framebuffer_address=0xE0000000,
            framebuffer_width=640,
            framebuffer_height=480,
            framebuffer_pitch=2560,
            framebuffer_bpp=32,
        )
        flags = FLAG_MEMORY_MAP | FLAG_BOOT_DRIVE | FLAG_FRAMEBUFFER | FLAG_KERNEL
        validate_context(BootContext(TBP_MAGIC, flags, info))

    def test_parse_context_decodes_and_checks(self) -> None:
        info = blank_info(boot_drive=0x80)
        context = parse_context(TBP_MAGIC, FLAG_BOOT_DRIVE, info.to_bytes())
        self.assertEqual(context.info.boot_drive, 0x80)

    def test_description_lists_capabilities(self) -> None:
        context = BootContext(TBP_MAGIC, FLAG_BOOT_DRIVE, blank_info(boot_drive=0x80))
        text = describe_context(context)
        self.assertIn("boot-drive", text)
        self.assertIn("0x80", text)


if __name__ == "__main__":
    unittest.main()
