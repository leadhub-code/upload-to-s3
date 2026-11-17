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

## Releasing a new version

The version is hardcoded in several places; all of them must be updated together.

1. Pick the new version `X.Y.Z` per the rules above (check `git log vPREV..HEAD`).
2. Update the version in:
   - `upload_to_s3.py` – `__version__ = 'X.Y.Z'`
   - `pyproject.toml` – `version = "X.Y.Z"`
   - `README.md` – all `@vPREV` / `/vPREV.zip` references in the Installation section
     (`grep -n 'vPREV' README.md`)
3. Run `uv lock` to update the version of the `upload-to-s3` package in `uv.lock` (never edit it by hand).
4. Verify: `make lint check` (the smoke tests check that `__version__` matches `pyproject.toml`
   and that `upload_to_s3 --version` works).
5. Commit: `git commit -am "chore(release): vX.Y.Z"`.
6. Create an annotated tag on that commit: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
7. Push the commit and the tag: `git push origin main vX.Y.Z`.
