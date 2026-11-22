#!/usr/bin/env python3
"""Inspect a 32-bit i386 executable without loading or executing it."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from elf32 import ELFError, describe_elf, parse_elf32


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and describe a Thorn-compatible ELF32 executable."
    )
    parser.add_argument("file", type=Path, help="ELF32 executable to inspect")
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    args = parser.parse_args(argv)

    try:
        image = parse_elf32(args.file)
    except (ELFError, OSError) as exc:
        print(f"inspect-elf: {exc}", file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "file": str(args.file),
            "file_size": image.file_size,
            "entry": image.header.entry,
            "machine": image.header.machine,
            "segments": [
                {
                    "index": segment.index,
                    "type": segment.segment_type,
                    "offset": segment.offset,
                    "physical_address": segment.physical_address,
                    "virtual_address": segment.virtual_address,
                    "file_size": segment.file_size,
                    "memory_size": segment.memory_size,
                    "flags": segment.flags,
                    "alignment": segment.alignment,
                }
                for segment in image.load_segments
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(describe_elf(image))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
