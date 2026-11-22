# SPDX-License-Identifier: GPL-2.0-or-later
#!/usr/bin/env python3
"""Validate and inspect a Thorn .mod file without executing its payload."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from modfile import ModuleError, describe_mod, parse_mod


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and describe a Thorn raw machine-code module."
    )
    parser.add_argument("file", type=Path, help="Thorn .mod file to inspect")
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    args = parser.parse_args(argv)

    try:
        module = parse_mod(args.file)
    except (ModuleError, OSError) as exc:
        print(f"inspect-mod: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "file": str(args.file),
                    "format_version": module.version,
                    "architecture": "i386",
                    "flags": module.flags,
                    "position_independent": True,
                    "file_size": module.file_size,
                    "payload_size": module.payload_size,
                    "entry_offset": module.entry_offset,
                    "payload_crc32": module.payload_crc32,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(describe_mod(module))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
