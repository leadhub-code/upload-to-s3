# upload-to-s3

Single-module CLI tool (`upload_to_s3.py`), managed with uv. See README.md for usage and development commands.

The command is `upload-to-s3`; the old name `upload_to_s3` is kept in `[project.scripts]` for backward
compatibility (existing CI pipelines use it) but is no longer mentioned in README.md. Removing it is a breaking change.

## Versioning

We use [Semantic Versioning](https://semver.org/). While the version is `0.x.y`:

- breaking change (CLI options, exit codes, behavior, supported Python versions) → bump minor (`0.1.0` → `0.2.0`)
- new feature or bug fix → bump patch (`0.1.0` → `0.1.1`)

From `1.0.0` on, follow standard semver (breaking → major, feature → minor, fix → patch).
Commit messages follow Conventional Commits; a `!` or `BREAKING CHANGE:` since the last tag means a breaking change.

## Changelog

The changelog is the `Changelog` section at the end of README.md. Every user-visible change (feature, fix,
behavior change, new requirement on Python/dependencies/IAM permissions) adds an entry to `### Unreleased`
in the same commit. Entries start with `Added:`, `Changed:`, `Fixed:` or `Removed:`; breaking changes start
with `**Breaking:**`. Internal changes (CI, tests, refactoring, docs) do not get an entry.

## Releasing a new version

The version is hardcoded in several places; all of them must be updated together.

1. Pick the new version `X.Y.Z` per the rules above (check `### Unreleased` in README.md and `git log vPREV..HEAD`).
2. Update the version in:
   - `upload_to_s3.py` – `__version__ = 'X.Y.Z'`
   - `pyproject.toml` – `version = "X.Y.Z"`
   - `README.md` – all `vPREV` (tag) and `PREV` (wheel file name) references in the Installation section
     (`grep -n 'PREV' README.md`; leave the `### PREV - …` changelog heading as it is)
   - `README.md` changelog – rename `### Unreleased` to `### X.Y.Z - YYYY-MM-DD` (release date) and add
     a new empty `### Unreleased` section above it for the next version
3. Run `uv lock` to update the version of the `upload-to-s3` package in `uv.lock` (never edit it by hand).
4. Verify: `make lint check` (the smoke tests check that `__version__` matches `pyproject.toml`
   and that `upload_to_s3 --version` works; `tests/test_release_notes.py` checks that README.md has
   a non-empty changelog section for `__version__`).
5. Commit: `git commit -am "chore(release): vX.Y.Z"`.
6. Create an annotated tag on that commit: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
7. Push the commit and the tag: `git push origin main vX.Y.Z`.
8. The tag push triggers `.github/workflows/release.yml`: it checks that the tag matches the project version,
   extracts the `### X.Y.Z - …` changelog section from README.md using `scripts/release_notes.py`
   (fails if it is missing or empty),
   builds the wheel and sdist, attests their build provenance and creates the GitHub Release with them
   and `SHA256SUMS`; the release notes are the changelog section followed by GitHub-generated notes. Check that the workflow succeeded and the README install URLs work.

The package is not published to PyPI (it is an internal CI tool); the GitHub Release assets are the distribution.

Runtime dependencies are declared twice: in `pyproject.toml` (`[project] dependencies`) and in the PEP 723
`# /// script` header of `upload_to_s3.py` (used by `uv run upload_to_s3.py`). Keep them in sync.
