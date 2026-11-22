# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests for the Thorn image inspection helpers."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.thorn_image import (
    BOOT_SIGNATURE,
    IMAGE_SIZE,
    STAGE1_SIZE,
    STAGE2_CAPACITY,
    ImageError,
    check_many,
    format_report,
    has_boot_signature,
    inspect_image,
    split_image,
    validate_image,
)


def make_image(stage2: bytes = b"stage-two") -> bytes:
    boot = bytearray(STAGE1_SIZE)
    boot[510:512] = BOOT_SIGNATURE
    body = stage2.ljust(STAGE2_CAPACITY, b"\x00")
    return bytes(boot) + body


class SignatureTests(unittest.TestCase):
    def test_valid_signature(self) -> None:
        data = bytearray(STAGE1_SIZE)
        data[510:512] = BOOT_SIGNATURE
        self.assertTrue(has_boot_signature(bytes(data)))

    def test_wrong_signature(self) -> None:
        data = bytearray(STAGE1_SIZE)
        data[510:512] = b"\x00\x00"
        self.assertFalse(has_boot_signature(bytes(data)))

    def test_short_data_has_no_signature(self) -> None:
        self.assertFalse(has_boot_signature(b"short"))

    def test_signature_at_wrong_offset_is_rejected(self) -> None:
        data = bytearray(STAGE1_SIZE)
        data[508:510] = BOOT_SIGNATURE
        self.assertFalse(has_boot_signature(bytes(data)))


class SplitTests(unittest.TestCase):
    def test_split_returns_one_sector_and_stage_two(self) -> None:
        data = make_image(b"payload")
        first, second = split_image(data)
        self.assertEqual(len(first), STAGE1_SIZE)
        self.assertEqual(len(second), STAGE2_CAPACITY)

    def test_short_image_is_rejected(self) -> None:
        with self.assertRaises(ImageError):
            split_image(b"x" * 100)

    def test_empty_stage_two_is_allowed_by_split(self) -> None:
        first, second = split_image(b"x" * STAGE1_SIZE)
        self.assertEqual(len(first), STAGE1_SIZE)
        self.assertEqual(second, b"")


class InspectionTests(unittest.TestCase):
    def test_valid_image_report(self) -> None:
        report = inspect_image(make_image())
        self.assertTrue(report.valid)
        self.assertEqual(report.image_size, IMAGE_SIZE)
        self.assertTrue(report.boot_signature_valid)

    def test_stage_two_capacity_is_reported(self) -> None:
        report = inspect_image(make_image())
        self.assertEqual(report.stage2_capacity, STAGE2_CAPACITY)

    def test_path_is_preserved(self) -> None:
        report = inspect_image(make_image())
        self.assertEqual(str(report.path), "<memory>")

    def test_stage_one_is_exactly_one_sector(self) -> None:
        report = inspect_image(make_image())
        self.assertEqual(report.stage1_size, 512)

    def test_report_dictionary_contains_status(self) -> None:
        report = inspect_image(make_image())
        self.assertTrue(report.as_dict()["valid"])

    def test_format_report_contains_result(self) -> None:
        report = inspect_image(make_image())
        rendered = format_report(report)
        self.assertIn("Result: PASS", rendered)
        self.assertIn("Stage 2 capacity", rendered)


class ValidationTests(unittest.TestCase):
    def test_valid_image_passes(self) -> None:
        report = validate_image(make_image())
        self.assertTrue(report.valid)

    def test_missing_signature_fails(self) -> None:
        data = bytearray(make_image())
        data[510:512] = b"\x00\x00"
        with self.assertRaisesRegex(ImageError, "boot signature"):
            validate_image(bytes(data))

    def test_truncated_image_fails(self) -> None:
        with self.assertRaisesRegex(ImageError, "expected exactly"):
            validate_image(make_image()[:-1])

    def test_oversized_image_fails(self) -> None:
        with self.assertRaisesRegex(ImageError, "expected exactly"):
            validate_image(make_image() + b"x")

    def test_empty_input_fails(self) -> None:
        with self.assertRaises(ImageError):
            validate_image(b"")

    def test_file_read_failure_is_reported(self) -> None:
        with self.assertRaises(ImageError):
            validate_image(Path("/definitely/not/a/thorn/image"))


class BatchTests(unittest.TestCase):
    def test_batch_keeps_success_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / "good.img"
            bad = Path(directory) / "bad.img"
            good.write_bytes(make_image())
            bad.write_bytes(b"broken")
            results = check_many([good, bad])
            self.assertEqual(len(results), 2)
            self.assertFalse(isinstance(results[0][1], Exception))
            self.assertTrue(isinstance(results[1][1], Exception))

    def test_batch_empty_input(self) -> None:
        self.assertEqual(check_many([]), [])


if __name__ == "__main__":
    unittest.main()
