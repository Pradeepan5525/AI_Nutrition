"""Color token enforcer: Verifies that no hex colors outside the strict token table appear in web/src/.

Approved design tokens:
    --bg:            #F6F8FA
    --surface:       #FFFFFF
    --border:        #E5E9EE
    --text:          #0F172A
    --muted:         #64748B
    --primary:       #047857
    --primary-hover: #065F46
    --primary-soft:  #ECFDF5
    --primary-accent:#10B981
    --hero-from:     #064E3B
    --hero-to:       #0B1F1A
    --warning:       #B45309
    --warning-soft:  #FEF3C7
    --danger:        #B91C1C
    --danger-soft:   #FEE2E2
"""

import re
import sys
from pathlib import Path

APPROVED_HEX = {
    "#f6f8fa",
    "#ffffff",
    "#e5e9ee",
    "#0f172a",
    "#64748b",
    "#047857",
    "#065f46",
    "#ecfdf5",
    "#10b981",
    "#064e3b",
    "#0b1f1a",
    "#b45309",
    "#fef3c7",
    "#b91c1c",
    "#fee2e2",
}

HEX_REGEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")


def check_colors(src_dir: Path) -> int:
    if not src_dir.exists():
        print(f"Warning: {src_dir} does not exist yet. Skipping check.")
        return 0

    violations = []
    extensions = {".css", ".ts", ".tsx", ".js", ".jsx", ".html"}

    for path in src_dir.rglob("*"):
        if path.is_file() and path.suffix in extensions:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(content.splitlines(), start=1):
                # Ignore comments if line starts with // or /*
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("/*"):
                    continue

                for match in HEX_REGEX.finditer(line):
                    raw_hex = match.group(0).lower()
                    # Expand 3-digit hex to 6-digit for canonical comparison if necessary
                    canonical_hex = raw_hex
                    if len(raw_hex) == 4:
                        canonical_hex = "#" + "".join(c * 2 for c in raw_hex[1:])

                    if canonical_hex not in APPROVED_HEX:
                        violations.append((path, line_no, raw_hex, stripped))

    if violations:
        print(f"FAIL: Found {len(violations)} unapproved hex color(s) outside design tokens:\n")
        for path, line_no, raw_hex, line_content in violations:
            print(f"  {path}:{line_no} -> {raw_hex}")
            print(f"    Line: {line_content}\n")
        print("Allowed tokens are:")
        for h in sorted(APPROVED_HEX):
            print(f"  {h.upper()}")
        return 1

    print("PASS: All colors in web/src/ conform strictly to the 12 design system tokens.")
    return 0


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    web_src = repo_root / "web" / "src"
    sys.exit(check_colors(web_src))
