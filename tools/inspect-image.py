# SPDX-License-Identifier: GPL-2.0-or-later
#!/usr/bin/env python3
"""Command-line inspector for Thorn BIOS disk images."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from thorn_image import ImageError, check_many, format_report, validate_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inspect-image.py",
        description="Validate Thorn's fixed-layout raw BIOS disk image.",
    )
    parser.add_argument(
        "images",
        nargs="+",
        type=Path,
        help="raw BIOS image file(s) to inspect",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON reports",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only failures",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    failed = False
    results = check_many(args.images)

    if args.json:
        payload = []
        for path, result in results:
            if isinstance(result, Exception):
                payload.append({"path": str(path), "valid": False, "error": str(result)})
                failed = True
            else:
                payload.append(result.as_dict())
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if failed else 0

    for path, result in results:
        if isinstance(result, Exception):
            failed = True
            if not args.quiet:
                print(f"FAIL {path}: {result}", file=sys.stderr)
            continue

        if not result.valid:
            failed = True
        if not args.quiet or not result.valid:
            print(format_report(result))
            print()

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
