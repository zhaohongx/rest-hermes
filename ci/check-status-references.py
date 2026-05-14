#!/usr/bin/env python3
"""
Check that active-status files do not reference beta/preview-status files.

Rules:
  active   -> active           OK
  active   -> beta/preview     BLOCK
  beta     -> beta/preview     OK
  preview  -> preview          OK

Exit: 0=pass, 1=violations
"""
import re
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIRS = [ROOT / "skills", ROOT / "docs"]

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
REF_RE = re.compile(r"@reference:\s*([^\s\)]+)|\[[^\]]+\]\(([^)]+\.md)\)")


def parse_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def extract_references(path: Path) -> list[Path]:
    text = path.read_text(encoding="utf-8")
    refs = []
    for m in REF_RE.finditer(text):
        ref = m.group(1) or m.group(2)
        if not ref or ref.startswith("http"):
            continue
        target = (path.parent / ref).resolve()
        if target.exists() and target.suffix == ".md":
            refs.append(target)
    return refs


def main() -> int:
    violations = []
    md_files = []
    for d in SKILLS_DIRS:
        if d.exists():
            md_files.extend(d.rglob("*.md"))

    # Build status map — default 'active' if no frontmatter
    status_map = {}
    for f in md_files:
        fm = parse_frontmatter(f)
        status_map[f] = fm.get("status", "active")

    for f in md_files:
        f_status = status_map[f]
        if f_status != "active":
            continue
        for ref in extract_references(f):
            ref_status = status_map.get(ref, "active")
            if ref_status in ("beta", "preview"):
                violations.append((f, f_status, ref, ref_status))

    if violations:
        print("FAIL: Status reference violations found:\n")
        for src, ss, tgt, ts in violations:
            print(f"  {src.relative_to(ROOT)} ({ss})")
            print(f"    -> {tgt.relative_to(ROOT)} ({ts})\n")
        return 1

    print(f"OK: All {len(md_files)} files passed status reference check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
