#!/usr/bin/env python3
"""
Print the changelog section of the given version from README.md.

Used by .github/workflows/release.yml to get the GitHub Release notes:

    python3 scripts/release_notes.py 0.1.0

The section starts with the heading "### X.Y.Z - YYYY-MM-DD" and ends before the next heading.
Exits with an error if the section is missing or empty.
"""

from argparse import ArgumentParser
from pathlib import Path
import re
import sys


readme_path = Path(__file__).resolve().parent.parent / 'README.md'


def main():
    p = ArgumentParser(description='Print the changelog section of the given version from README.md.')
    p.add_argument('version', help='version without the "v" prefix, e.g. 0.1.0')
    args = p.parse_args()
    notes = get_release_notes(readme_path.read_text(), args.version)
    if not notes:
        sys.exit(f'No changelog entries for {args.version} in README.md (expected section "### {args.version} - ...")')
    print(notes)


def get_release_notes(readme, version):
    """
    Return the changelog section of the given version without its heading, or None if it is missing or empty.
    """
    heading = rf'^### {re.escape(version)}(?: [^\n]*)?\n'
    # the section ends before the next ATX heading ("# ...") or setext heading ("Title\n-----"), or at end of file
    end = r'(?=^#|^[^\n]+\n(?:-+|=+)[ \t]*$|\Z)'
    m = re.search(heading + r'(.*?)' + end, readme, re.MULTILINE | re.DOTALL)
    return (m and m.group(1).strip()) or None


if __name__ == '__main__':
    main()
