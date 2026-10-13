#!/usr/bin/env python3
"""Install this local skill for Codex and Claude Code without downloading it."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from install import (
    SKILL_FILES,
    VERSION,
    claude_link_for,
    ensure_claude_link,
    install_skill,
    print_install_result,
    record_install,
    repo_target,
    validate_claude_link,
)


def local_payloads(source: Path) -> dict[str, bytes]:
    """Copy the working tree's packaged files, including uncommitted edits."""
    return {relative: (source / relative).read_bytes() for relative in SKILL_FILES}


def install_local(source: Path, root: Path, update: bool) -> Path:
    """Use the standard staged validation and rollback for a local installation."""
    target, scope_root = repo_target(root)
    link = claude_link_for(target, scope_root)
    validate_claude_link(link, target)
    versions = install_skill(target, local_payloads(source), update)
    ensure_claude_link(link, target)
    record_install(target)
    print_install_result(target, update, link, *versions)
    print(f"Read {target}/SKILL.md and continue setup in this chat, before handoff.")
    return target


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="destination project")
    parser.add_argument(
        "--update", action="store_true", help="replace a managed installation"
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        install_local(
            Path(__file__).resolve().parent.parent, Path(args.root), args.update
        )
    except (OSError, RuntimeError, ValueError, SyntaxError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
