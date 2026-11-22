# SPDX-License-Identifier: GPL-2.0-or-later
#!/usr/bin/env python3
"""Package a raw i386 machine-code binary as a Thorn .mod file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from modfile import ModuleError, build_mod


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Package position-independent raw i386 code as a Thorn .mod file."
    )
    parser.add_argument("input", type=Path, help="raw machine-code input")
    parser.add_argument("output", type=Path, help="output .mod file")
    parser.add_argument(
        "--entry-offset",
        type=lambda value: int(value, 0),
        default=0,
        help="entry-point offset within the raw payload (default: 0)",
    )
    args = parser.parse_args(argv)

    try:
        payload = args.input.read_bytes()
        module = build_mod(payload, args.entry_offset)
        args.output.write_bytes(module)
    except (OSError, ModuleError, ValueError) as exc:
        print(f"pack-mod: {exc}", file=sys.stderr)
        return 1

    print(
        f"Packed {len(payload)} bytes into {args.output} "
        f"(entry offset 0x{args.entry_offset:x})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
