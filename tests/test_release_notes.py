"""
Tests of scripts/release_notes.py that extracts GitHub Release notes from the README changelog.
"""

import importlib.util
from pathlib import Path
from subprocess import run
import sys

import upload_to_s3


script_path = Path(__file__).resolve().parent.parent / 'scripts' / 'release_notes.py'

spec = importlib.util.spec_from_file_location('release_notes', script_path)
release_notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_notes)
get_release_notes = release_notes.get_release_notes


sample_readme = """\
Example
=======

Changelog
---------

Intro text.

### Unreleased

### 1.10.0 - 2026-02-01

- Added: foo.
  Continuation line.

- Fixed: bar.

### 1.1.0 - 2026-01-01

- Fixed: baz.

### 1.0.0

### 0.9.0 - 2025-12-01

- Initial release.


Next section
------------

Not part of the changelog.
"""


def test_section():
    assert get_release_notes(sample_readme, '1.10.0') == '- Added: foo.\n  Continuation line.\n\n- Fixed: bar.'
    assert get_release_notes(sample_readme, '1.1.0') == '- Fixed: baz.'


def test_last_section_ends_before_next_setext_heading():
    assert get_release_notes(sample_readme, '0.9.0') == '- Initial release.'


def test_last_section_ends_at_end_of_file():
    assert get_release_notes('### 1.0.0 - 2026-01-01\n\n- Foo.\n', '1.0.0') == '- Foo.'


def test_empty_section():
    assert get_release_notes(sample_readme, 'Unreleased') is None
    assert get_release_notes(sample_readme, '1.0.0') is None


def test_missing_section():
    assert get_release_notes(sample_readme, '2.0.0') is None
    assert get_release_notes(sample_readme, '1.1') is None  # not a prefix match of 1.1.0
    assert get_release_notes(sample_readme, '1.1.0.0') is None
    assert get_release_notes(sample_readme, '1x10x0') is None  # dots are not regex wildcards


def test_readme_has_changelog_section_for_current_version():
    """
    Catches forgetting to rename "### Unreleased" when releasing a new version
    (the release workflow would fail on the tag push).
    """
    cp = run([sys.executable, str(script_path), upload_to_s3.__version__], check=True, capture_output=True, text=True)
    assert cp.stdout.strip()


def test_script_fails_for_missing_version():
    cp = run([sys.executable, str(script_path), '99.0.0'], capture_output=True, text=True)
    assert cp.returncode == 1
    assert cp.stdout == ''
    assert 'No changelog entries for 99.0.0' in cp.stderr
