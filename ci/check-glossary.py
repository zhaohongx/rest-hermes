#!/usr/bin/env python3
"""
Scan all markdown files for glossary spelling violations.

Exit: 0=pass, 1=violations
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Canonical spelling -> list of wrong regex patterns
GLOSSARY = {
    "SpecDocument": [r"\bSpeDocument\b", r"\bSpec Document\b", r"\bspecdocument\b"],
    "formalize": [r"\bFormalize\b", r"\bformalise\b"],
    "intent-classifier": [r"\bIntentClassifier\b", r"\bintent_classifier\b", r"\bIntent Classifier\b"],
    "Hermes": [r"(?<!-)hermes\b(?![-.])", r"\bHERMES\b"],
    "Hermes Agent": [r"\bhermes agent\b", r"\bHermesAgent\b"],
    "SKILL.md": [r"\bskill\.md\b", r"\bSkill\.md\b"],
    "exposed_tools": [r"\bexposedTools\b", r"\bExposedTools\b"],
    "orchestrator": [r"\bOrchestrator\b", r"\borchastrator\b"],
}


def main() -> int:
    violations = []
    for f in ROOT.rglob("*.md"):
        # Skip generated/vendored files
        parts = set(f.parts)
        if parts & {".git", ".claude", "node_modules", "__pycache__", ".venv"}:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for canonical, wrong_patterns in GLOSSARY.items():
            for pat in wrong_patterns:
                for m in re.finditer(pat, text):
                    line_no = text[: m.start()].count("\n") + 1
                    violations.append((f, line_no, m.group(), canonical))

    if violations:
        print("FAIL: Glossary violations found:\n")
        for f, ln, wrong, right in violations:
            print(f"  {f.relative_to(ROOT)}:{ln}  '{wrong}' -> should be '{right}'")
        print(f"\n  Total: {len(violations)} violations")
        return 1

    print("OK: Glossary check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
