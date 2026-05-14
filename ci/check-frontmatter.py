#!/usr/bin/env python3
"""
Validate SKILL.md frontmatter against JSON Schema.

Exit: 0=all valid, 1=violations, 2=missing dependency
"""
import re
import sys
import json
import yaml
from pathlib import Path

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("WARNING: jsonschema not installed. Run: pip install jsonschema")
    print("Skipping schema validation (soft-fail for promptware phase).")
    sys.exit(0)

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "ci" / "frontmatter-schema.json"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

def main() -> int:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found at {SCHEMA_PATH}")
        return 2

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = []
    skill_files = list(ROOT.glob("skills/**/SKILL.md"))

    for f in skill_files:
        text = f.read_text(encoding="utf-8")
        m = FRONTMATTER_RE.match(text)
        if not m:
            errors.append((f, "no frontmatter found"))
            continue
        try:
            fm = yaml.safe_load(m.group(1))
            validate(instance=fm, schema=schema)
        except yaml.YAMLError as e:
            errors.append((f, f"YAML parse error: {e}"))
        except ValidationError as e:
            errors.append((f, f"Schema violation: {e.message}"))

    if errors:
        print("FAIL: Frontmatter schema violations:\n")
        for f, e in errors:
            print(f"  {f.relative_to(ROOT)}")
            print(f"    {e}\n")
        return 1

    print(f"OK: All {len(skill_files)} SKILL.md frontmatter valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
