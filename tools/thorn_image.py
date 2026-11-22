# SPDX-License-Identifier: GPL-2.0-or-later
#!/usr/bin/env python3
"""Validation helpers for Thorn's raw BIOS disk image.

This module intentionally performs host-side inspection only. It does not
modify images, invoke emulators, or make assumptions about a running machine.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SECTOR_SIZE = 512
BOOT_SIGNATURE = b"\x55\xaa"
STAGE1_SIZE = SECTOR_SIZE
STAGE2_LBA = 1
STAGE2_SECTORS = 32
STAGE2_CAPACITY = STAGE2_SECTORS * SECTOR_SIZE
IMAGE_SIZE = STAGE1_SIZE + STAGE2_CAPACITY


class ImageError(ValueError):
    """Raised when a Thorn image violates the documented disk layout."""


@dataclass(frozen=True)
class ImageReport:
    """Facts discovered while inspecting a Thorn raw image."""

    path: Path
    image_size: int
    boot_signature_valid: bool
    stage1_size: int
    stage2_nonzero_bytes: int
    stage2_capacity: int
    trailing_bytes: int

    @property
    def valid(self) -> bool:
        return (
            self.boot_signature_valid
            and self.stage1_size == STAGE1_SIZE
            and self.image_size == IMAGE_SIZE
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "image_size": self.image_size,
            "boot_signature_valid": self.boot_signature_valid,
            "stage1_size": self.stage1_size,
            "stage2_nonzero_bytes": self.stage2_nonzero_bytes,
            "stage2_capacity": self.stage2_capacity,
            "trailing_bytes": self.trailing_bytes,
            "valid": self.valid,
        }


def _read_bytes(source: Path | str | bytes | bytearray) -> tuple[bytes, Path]:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source), Path("<memory>")
    path = Path(source)
    try:
        return path.read_bytes(), path
    except OSError as exc:
        raise ImageError(f"cannot read image {path}: {exc}") from exc


def has_boot_signature(data: bytes) -> bool:
    """Return whether bytes 510 and 511 contain the BIOS boot signature."""
    return len(data) >= STAGE1_SIZE and data[510:512] == BOOT_SIGNATURE


def split_image(data: bytes) -> tuple[bytes, bytes]:
    """Split a raw image into its boot sector and Stage 2 storage area."""
    if len(data) < STAGE1_SIZE:
        raise ImageError(
            f"image is shorter than one sector ({len(data)} < {STAGE1_SIZE})"
        )
    return data[:STAGE1_SIZE], data[STAGE1_SIZE:]


def inspect_image(source: Path | str | bytes | bytearray) -> ImageReport:
    """Inspect the fixed-size Thorn BIOS image layout."""
    data, path = _read_bytes(source)
    stage1, stage2_area = split_image(data)
    stage2 = stage2_area.rstrip(b"\x00")
    signature = has_boot_signature(stage1)
    report = ImageReport(
        path=path,
        image_size=len(data),
        boot_signature_valid=signature,
        stage1_size=len(stage1),
        stage2_nonzero_bytes=sum(byte != 0 for byte in stage2_area),
        stage2_capacity=STAGE2_CAPACITY,
        trailing_bytes=max(0, len(data) - IMAGE_SIZE),
    )
    return report


def validate_image(source: Path | str | bytes | bytearray) -> ImageReport:
    """Inspect an image and raise ImageError when its layout is invalid."""
    report = inspect_image(source)
    problems: list[str] = []
    if not report.boot_signature_valid:
        problems.append("missing 0xAA55 boot signature")
    if report.image_size != IMAGE_SIZE:
        problems.append(
            f"image is {report.image_size} bytes; expected exactly {IMAGE_SIZE}"
        )
    if problems:
        raise ImageError("; ".join(problems))
    return report


def format_report(report: ImageReport) -> str:
    """Render a stable, human-readable validation summary."""
    status = "PASS" if report.valid else "FAIL"
    lines = [
        f"Thorn image: {report.path}",
        f"Result: {status}",
        f"Image size: {report.image_size} bytes",
        f"Stage 1: {report.stage1_size} bytes",
        f"Boot signature: {'valid' if report.boot_signature_valid else 'invalid'}",
        f"Stage 2 capacity: {report.stage2_capacity} bytes",
        f"Non-zero bytes in Stage 2 area: {report.stage2_nonzero_bytes}",
    ]
    if report.trailing_bytes:
        lines.append(f"Bytes beyond image layout: {report.trailing_bytes}")
    return "\n".join(lines)


def check_many(paths: Iterable[Path | str]) -> list[tuple[Path, ImageReport | Exception]]:
    """Inspect multiple images without stopping after the first failure."""
    results: list[tuple[Path, ImageReport | Exception]] = []
    for item in paths:
        path = Path(item)
        try:
            results.append((path, validate_image(path)))
        except (ImageError, OSError) as exc:
            results.append((path, exc))
    return results
