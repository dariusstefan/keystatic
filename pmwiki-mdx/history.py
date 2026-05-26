#!/usr/bin/env python3
"""Reconstruct PMWiki page history from a page file.

PMWiki stores the current page text plus normal-diff hunks between revisions.
The diff keys look like:

    diff:<new_timestamp>:<old_timestamp>[:flags]=...

The diff body compares the newer text on the left (`<`) to the older text on
the right (`>`). Starting from the current `text=...`, we can walk backwards by
applying the right side of each diff.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from convert import extract_description, pmwiki_to_mdx, yaml_quote


@dataclass
class DiffEntry:
    new_ts: int
    old_ts: int
    flags: str
    body: str


@dataclass
class Hunk:
    left_start: int
    left_end: int
    op: str
    right_lines: list[str]


def decode(value: str) -> str:
    return unquote(value, encoding="latin-1")


def parse_page(path: Path) -> tuple[dict[str, str], list[DiffEntry]]:
    meta: dict[str, str] = {}
    diffs: list[DiffEntry] = []

    with path.open(encoding="latin-1") as f:
        for raw in f:
            line = raw.rstrip("\n")
            key, sep, value = line.partition("=")
            if not sep:
                continue

            match = re.fullmatch(r"diff:(\d+):(\d+)(?::(.*))?", key)
            if match:
                diffs.append(
                    DiffEntry(
                        new_ts=int(match.group(1)),
                        old_ts=int(match.group(2)),
                        flags=match.group(3) or "",
                        body=decode(value),
                    )
                )
                continue

            if key not in meta:
                meta[key] = decode(value)

    diffs.sort(key=lambda diff: diff.new_ts, reverse=True)
    return meta, diffs


def parse_range(start: str, end: str | None) -> tuple[int, int]:
    first = int(start)
    return first, int(end or start)


def parse_diff_hunks(body: str) -> list[Hunk]:
    if not body.strip():
        return []

    lines = body.splitlines()
    hunks: list[Hunk] = []
    i = 0

    while i < len(lines):
        command = lines[i]
        i += 1
        if command.startswith("\\ "):
            continue
        match = re.fullmatch(r"(\d+)(?:,(\d+))?([acd])(\d+)(?:,(\d+))?", command)
        if not match:
            raise ValueError(f"Unsupported diff command: {command!r}")

        left_start, left_end = parse_range(match.group(1), match.group(2))
        op = match.group(3)
        right_lines: list[str] = []

        if op in {"c", "d"}:
            while i < len(lines) and (lines[i].startswith("< ") or lines[i].startswith("\\ ")):
                i += 1

        if op == "c":
            if i >= len(lines) or lines[i] != "---":
                raise ValueError(f"Expected diff separator after {command!r}")
            i += 1

        if op in {"a", "c"}:
            while i < len(lines) and (lines[i].startswith("> ") or lines[i].startswith("\\ ")):
                if lines[i].startswith("> "):
                    right_lines.append(lines[i][2:])
                i += 1

        hunks.append(Hunk(left_start, left_end, op, right_lines))

    return hunks


def apply_reverse_diff(text: str, body: str) -> str:
    lines = text.splitlines()

    for hunk in reversed(parse_diff_hunks(body)):
        if hunk.op == "a":
            lines[hunk.left_start:hunk.left_start] = hunk.right_lines
        elif hunk.op == "d":
            del lines[hunk.left_start - 1:hunk.left_end]
        elif hunk.op == "c":
            lines[hunk.left_start - 1:hunk.left_end] = hunk.right_lines
        else:
            raise ValueError(f"Unsupported diff operation: {hunk.op}")

    return "\n".join(lines)


def ts_label(timestamp: int) -> str:
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y%m%d-%H%M%S")


def write_snapshot(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")


def convert_snapshot(title: str, raw_text: str) -> str:
    body = pmwiki_to_mdx(raw_text)
    description = extract_description(body)
    frontmatter = [
        "---",
        f'title: "{yaml_quote(title)}"',
        f'description: "{yaml_quote(description)}"',
        "---",
        "",
    ]
    return "\n".join(frontmatter) + body


def reconstruct(path: Path, out_dir: Path, write_mdx: bool) -> None:
    meta, diffs = parse_page(path)
    current_ts = int(meta.get("time", "0"))
    title = meta.get("title", path.name)
    text = meta.get("text", "")
    page_dir = out_dir / path.name
    manifest = []

    def meta_for(timestamp: int, key: str) -> str:
        return meta.get(f"{key}:{timestamp}", meta.get(key, ""))

    def save(index: int, timestamp: int, content: str, source: str, flags: str = "") -> None:
        base = f"{index:03d}_{ts_label(timestamp)}_{timestamp}"
        raw_path = page_dir / "raw" / f"{base}.pmwiki"
        write_snapshot(raw_path, content)

        mdx_path = None
        if write_mdx:
            mdx_path = page_dir / "mdx" / f"{base}.mdx"
            write_snapshot(mdx_path, convert_snapshot(title, content))

        manifest.append(
            {
                "index": index,
                "timestamp": timestamp,
                "datetime_utc": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
                "source": source,
                "flags": flags,
                "author": meta_for(timestamp, "author"),
                "host": meta_for(timestamp, "host"),
                "summary": meta_for(timestamp, "csum"),
                "raw": str(raw_path),
                "mdx": str(mdx_path) if mdx_path else None,
            }
        )

    save(0, current_ts, text, "current")

    expected_ts = current_ts
    index = 1
    for diff in diffs:
        if diff.new_ts != expected_ts:
            continue
        text = apply_reverse_diff(text, diff.body)
        save(index, diff.old_ts, text, f"diff:{diff.new_ts}:{diff.old_ts}", diff.flags)
        expected_ts = diff.old_ts
        index += 1

    manifest_path = page_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Reconstructed {len(manifest)} snapshot(s) for {path.name}")
    print(f"  raw: {page_dir / 'raw'}")
    if write_mdx:
        print(f"  mdx: {page_dir / 'mdx'}")
    print(f"  manifest: {manifest_path}")

    return manifest


def git_commit_history(manifest: list[dict], target: Path) -> None:
    """Replay MDX snapshots as git commits, oldest first, with original dates."""
    target.parent.mkdir(parents=True, exist_ok=True)
    ordered = list(reversed(manifest))  # oldest → newest

    for entry in ordered:
        mdx_file = entry.get("mdx")
        if not mdx_file:
            print(f"  skip index {entry['index']}: no MDX file")
            continue

        content = Path(mdx_file).read_text(encoding="utf-8")
        target.write_text(content, encoding="utf-8")

        author = entry["author"] or "unknown"
        date = entry["datetime_utc"]
        summary = entry["summary"].strip() if entry["summary"].strip() else f"docs: {target.stem} ({entry['datetime_utc'][:10]})"

        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
        env["GIT_AUTHOR_NAME"] = author
        env["GIT_AUTHOR_EMAIL"] = f"{author}@opensips.org"
        env["GIT_COMMITTER_NAME"] = author
        env["GIT_COMMITTER_EMAIL"] = f"{author}@opensips.org"

        subprocess.run(["git", "add", str(target)], check=True)
        result = subprocess.run(["git", "commit", "-m", summary], env=env)
        if result.returncode == 0:
            print(f"  committed index {entry['index']} ({date[:10]}): {summary}")
        else:
            print(f"  skip index {entry['index']} ({date[:10]}): nothing to commit")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstruct PMWiki page history.")
    parser.add_argument("page", type=Path, help="PMWiki page file")
    parser.add_argument(
        "out_dir",
        type=Path,
        nargs="?",
        default=Path("pmwiki-mdx/history-output"),
        help="output directory",
    )
    parser.add_argument("--mdx", action="store_true", help="also convert each snapshot to MDX")
    parser.add_argument("--git", metavar="TARGET_PATH", type=Path,
                        help="replay history as git commits, writing MDX to TARGET_PATH")
    args = parser.parse_args()

    manifest = reconstruct(args.page, args.out_dir, args.mdx or args.git is not None)

    if args.git:
        print(f"\nReplaying {len(manifest)} commit(s) → {args.git}")
        git_commit_history(manifest, args.git)


if __name__ == "__main__":
    main()
