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
    "intent-classifier": [r"\bIntentClassifier\b", r"\bIntent Classifier\b"],
    # Note: intent_classifier (underscore) is legitimate in Prometheus metric names
    # Only flag standalone "hermes" as proper noun, not in technical identifiers
    "Hermes": [r"(?<![a-z-])hermes(?![a-z0-9_-])", r"\bHERMES\b"],
    "SKILL.md": [r"\bskill\.md\b", r"\bSkill\.md\b"],
    "exposed_tools": [r"\bexposedTools\b", r"\bExposedTools\b"],
    "orchestrator": [r"\bOrchestrator\b", r"\borchastrator\b"],
}

# Patterns that are legitimate technical uses of lowercase "hermes"
HERMES_LEGITIMATE_PATTERNS = [
    r"hermes-agent",        # package / project name
    r"hermes_cli",          # Python module
    r"hermes_constants",    # Python module
    r"hermes model",        # CLI command (lowercase is intentional for CLI)
    r"hermes config",       # CLI command
    r"hermes tools",        # CLI command
    r"hermes setup",        # CLI command
    r"hermes gateway",      # CLI command
    r"hermes status",       # CLI command
    r"hermes server",       # CLI command
    r"hermes\.[a-z]",       # CLI subcommand
    r"~?/\.hermes/",        # config path
    r"%APPDATA%\\\\hermes", # Windows path
    r"hermes-agent\.",      # URL / domain
    r"@hermes",             # mentions
    r"metadata.*hermes",    # YAML metadata key (metadata.hermes.tags etc)
    r"hermes:",             # YAML key in isolation
]

# Paths to skip entirely (legacy docs with known inconsistencies)
SKIP_PATHS = {
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "hermes-already-has-routines.md",
    "skills/software-development/glossary.md",  # documents wrong spellings intentionally
}

# Path prefixes to skip (entire subtrees with pre-existing inconsistencies)
SKIP_PREFIXES = [
    "RELEASE_v",         # historical release notes
    "README.zh-CN.md",   # Chinese README variant
    "SECURITY.md",       # legacy security policy
    ".github/",          # GitHub templates
    "plugins/",          # third-party plugins
    "environments/",     # environment READMEs
    "skills/apple/",     # legacy skills
    "skills/autonomous-ai-agents/",  # legacy skills (hermes-agent self-skill)
    "skills/creative/",  # legacy skills
    "skills/devops/",    # legacy skills
    "optional-skills/",  # externally sourced optional skills
]


def main() -> int:
    # Default mode: only scan software-development skills and root docs
    # (the files we actually own). Use --full for legacy repo sweep.
    scope_prefixes = [
        "skills/software-development/formalize/",
        "skills/software-development/intent-classifier/",
        "skills/software-development/hermes-agent-skill-authoring/",
        "docs/beta-program/",
        "ci/",
        "CHANGELOG.md",
        "glossary.md",
    ]
    full_scan = "--full" in sys.argv

    violations = []
    for f in ROOT.rglob("*.md"):
        # Skip generated/vendored files
        parts = set(f.parts)
        if parts & {".git", ".claude", "node_modules", "__pycache__", ".venv"}:
            continue
        # In default mode, only scan files we own
        rel = str(f.relative_to(ROOT)).replace("\\", "/")
        if not full_scan:
            if not any(rel.startswith(p) for p in scope_prefixes):
                continue
        if rel in SKIP_PATHS:
            continue
        if any(rel.startswith(p) for p in SKIP_PREFIXES):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for canonical, wrong_patterns in GLOSSARY.items():
            for pat in wrong_patterns:
                for m in re.finditer(pat, text):
                    matched_text = m.group()
                    # Skip legitimate technical uses
                    if canonical == "Hermes":
                        # Check if this occurrence is part of a legitimate pattern
                        ctx_start = max(0, m.start() - 20)
                        ctx_end = min(len(text), m.end() + 20)
                        context = text[ctx_start:ctx_end]
                        if any(re.search(lp, context) for lp in HERMES_LEGITIMATE_PATTERNS):
                            continue
                    line_no = text[: m.start()].count("\n") + 1
                    violations.append((f, line_no, matched_text, canonical))

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
