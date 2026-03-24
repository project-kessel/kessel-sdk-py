---
name: release-python-sdk
description: Release a new version of the Kessel Python SDK (kessel-sdk). Guides through version bump, code generation, quality checks, build, publish to PyPI, git tagging, and GitHub release creation. Use when the user wants to release, publish, bump version, or cut a new release of the Python SDK.
---

# Release Kessel Python SDK

## Prerequisites

- Write access to the GitHub repository
- PyPI account with publish access to `kessel-sdk`
- Python 3.11+, `buf`, `build`, and `twine` installed

```bash
pip install build twine
pip install "kessel-sdk[dev]"
```

## Release Process

### Step 1: Update the Version

Edit the `version` field in `pyproject.toml` to the new version number, following [Semantic Versioning](https://semver.org/):
- **MAJOR**: incompatible API changes
- **MINOR**: backward-compatible new functionality
- **PATCH**: backward-compatible bug fixes

Then set the `VERSION` env var from `pyproject.toml` for use in subsequent steps:

```bash
export VERSION=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
echo "Releasing version: ${VERSION}"
```

### Step 2: Update Dependencies (if needed)

```bash
buf generate
```

### Step 3: Run Quality Checks

```bash
black --exclude '.*_pb2(_grpc)?\.py' src/ examples/
flake8 --exclude '*_pb2.py,*_pb2_grpc.py' src/ examples/
python -c "import examples.check"
python -c "import examples.auth"
pytest
python -m build
```

### Step 4: Review Changes

Before committing, summarize the release for the user and ask for confirmation.

1. Run `git diff --stat` and `git status` to gather all pending changes.
2. Compare `$VERSION` against the latest git tag (`git describe --tags --abbrev=0`) to determine the bump type (major/minor/patch).
3. Present a summary to the user including:
   - The version being released and the bump type
   - List of files that will be committed
   - Quality check results
4. **Wait for user confirmation before proceeding.**

### Step 5: Commit and Push

```bash
git add pyproject.toml
git commit -m "chore: bump version to ${VERSION}"
git push origin main
```

Include any other changed files (generated code, lock files) in the commit.

### Step 6: Build and Publish to PyPI

```bash
rm -rf dist/ build/
python -m build
```

Before publishing, show the built artifacts (`ls -lh dist/`) and **ask the user to confirm** before running `twine upload`, since PyPI publishes are effectively irreversible.

```bash
twine upload dist/*
```

### Step 7: Tag the Release

```bash
git tag -a v${VERSION} -m "Release version ${VERSION}"
git push origin v${VERSION}
```

### Step 8: Create GitHub Release

```bash
gh release create v${VERSION} --title "v${VERSION}" --generate-notes
```

Or manually:
- Go to the [GitHub Releases page](https://github.com/project-kessel/kessel-sdk-py/releases)
- Click "Create a new release"
- Select the tag you just created
- Add release notes describing the changes
- Publish the release

## Quick Reference Checklist

```
Release v${VERSION}:
- [ ] Update version in pyproject.toml and derive VERSION from it
- [ ] Regenerate gRPC code if needed (buf generate)
- [ ] Run black, flake8, example imports, pytest
- [ ] Build succeeds (python -m build)
- [ ] Review changes and get user confirmation
- [ ] Commit and push version bump
- [ ] Clean build, confirm with user, publish to PyPI
- [ ] Create and push git tag (v${VERSION})
- [ ] Create GitHub release
```
