#!/usr/bin/env python3
"""Generate contributor sections for all module docs.

Runs build-contrib.sh against the local opensips/ git clone for each module,
converts the generated contributors.xml to Markdown, and injects it at the
<!-- CONTRIBUTORS --> placeholder in src/content/docs/modules/devel/<module>.md.

Usage:
    python3 scripts/generate-contributors.py [module1 module2 ...]
    (no args = all modules found in src/content/docs/modules/devel/)
"""

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent.parent
OPENSIPS_DIR = ROOT / 'opensips'
MODULES_DEVEL = ROOT / 'src/content/docs/modules/devel'
PLACEHOLDER = '<!-- CONTRIBUTORS -->'

sys.path.insert(0, str(ROOT / 'pmwiki-mdx'))
from docbook_to_md import _Emitter, _inline


# ---------------------------------------------------------------------------
# Convert contributors.xml → Markdown
# ---------------------------------------------------------------------------

def _contrib_xml_to_md(xml_path: Path) -> str:
    """Parse contributors.xml and emit Markdown for the two chapters."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        print(f"  [WARN] XML parse error in {xml_path}: {e}", file=sys.stderr)
        return ''

    root = tree.getroot()
    emitter = _Emitter()

    # contributors.xml is a fragment (no <book> wrapper), so iterate top-level
    for child in root if root.tag != 'book' else root:
        tag = (child.tag or '').lower()
        chapter_id = (child.get('id') or '').lower()
        if tag == 'chapter' and chapter_id in ('contributors', 'documentation'):
            emitter._section(child, depth=2)

    return emitter.result()


# ---------------------------------------------------------------------------
# Run build-contrib.sh and inject result
# ---------------------------------------------------------------------------

def generate_for_module(module: str) -> bool:
    if not OPENSIPS_DIR.is_dir():
        print(f"  [ERROR] {OPENSIPS_DIR} not found — clone opensips repo first", file=sys.stderr)
        return False

    md_path = MODULES_DEVEL / f'{module}.md'
    if not md_path.exists():
        print(f"  [SKIP] {module}.md not found", file=sys.stderr)
        return False

    content = md_path.read_text('utf-8')
    if PLACEHOLDER not in content:
        return True  # nothing to inject

    print(f"  {module}")

    result = subprocess.run(
        ['bash', 'doc/build-contrib.sh', module],
        cwd=OPENSIPS_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [WARN] build-contrib.sh failed for {module}:\n{result.stderr[:300]}", file=sys.stderr)
        return False

    xml_path = OPENSIPS_DIR / 'modules' / module / 'doc' / 'contributors.xml'
    if not xml_path.exists():
        print(f"  [WARN] contributors.xml not found for {module}", file=sys.stderr)
        return False

    contrib_md = _contrib_xml_to_md(xml_path)
    if not contrib_md.strip():
        return True

    md_path.write_text(content.replace(PLACEHOLDER, contrib_md.strip()), 'utf-8')
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not MODULES_DEVEL.exists():
        print("Run npm run generate:modules first.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 1:
        modules = sys.argv[1:]
    else:
        modules = sorted(p.stem for p in MODULES_DEVEL.glob('*.md'))

    print(f"Generating contributors for {len(modules)} modules...")
    ok = sum(generate_for_module(m) for m in modules)
    print(f"Done ({ok}/{len(modules)} succeeded).")


if __name__ == '__main__':
    main()
