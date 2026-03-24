---
name: release-python-sdk
description: Release a new version of the Kessel Python SDK (kessel-sdk). Guides through version bump, code generation, quality checks, build, publish to PyPI, git tagging, and GitHub release creation. Use when the user wants to release, publish, bump version, or cut a new release of the Python SDK.
---

# Release Kessel Python SDK

## Prerequisites

- Write access to the GitHub repository
- PyPI account with publish access to `kessel-sdk`
- Python 3.11+, `buf`, `build`, and `twine` installed
- PyPI auth configured via `~/.pypirc` or `TWINE_USERNAME`/`TWINE_PASSWORD` env vars. Note: Cursor's shell may not inherit exported tokens -- if auth is not available, the `twine upload` step must be run manually in your own terminal.

```bash
pip install build twine
pip install "kessel-sdk[dev]"
```

## Release Process

### Step 0: Preflight -- Clean Working Tree

Run `git status --porcelain` to check for uncommitted changes. If the working tree is dirty, present the list of changed files and ask the user whether to:
1. Abort the release (recommended if unsure)
2. Stash changes for later: `git stash --include-untracked`

### Step 1: Update the Version and Create Release Branch

Edit the `version` field in `pyproject.toml` to the new version number, following [Semantic Versioning](https://semver.org/):
- **MAJOR**: incompatible API changes
- **MINOR**: backward-compatible new functionality
- **PATCH**: backward-compatible bug fixes

Then set the `VERSION` env var from `pyproject.toml` and create a release branch:

```bash
export VERSION=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
echo "Releasing version: ${VERSION}"
git checkout -b release/${VERSION}
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

### Step 4: Documentation Audit (optional)

Check if the README is up to date with the current codebase:

1. **Examples:** Compare the files in `examples/*.py` against the "Examples" section in the README. Flag any examples that exist on disk but are not listed in the README.
2. **Available Services:** If a local Kessel instance is running, list endpoints with `grpcurl -plaintext localhost:9081 list kessel.inventory.v1beta2.KesselInventoryService` and compare against the "Available Services" section in the README. Flag any undocumented endpoints.

Present any gaps to the user and ask if they'd like to update the README before releasing. Skip the grpcurl check if no local instance is available.

### Step 5: Review Changes

Before committing, summarize the release for the user and ask for confirmation.

1. Run `git diff --stat` and `git status` to gather all pending changes.
2. Compare `$VERSION` against the latest git tag (`git describe --tags --abbrev=0`) to determine the bump type (major/minor/patch).
3. Present a summary to the user including:
   - The version being released and the bump type
   - List of files that will be committed
   - Quality check results
4. **Wait for user confirmation before proceeding.**

### Step 6: Commit, Push Branch, and Create PR

```bash
git add pyproject.toml
git commit -m "chore: bump version to ${VERSION}"
git push -u origin release/${VERSION}
gh pr create --title "Release v${VERSION}" --body "Release version ${VERSION}"
```

Include any other changed files (generated code, lock files) in the commit.

**The remaining steps (publish, tag, GitHub release) should be performed after the PR is merged to main.**

### Step 7: Build and Publish to PyPI

After the PR is merged, switch back to main and pull:

```bash
git checkout main && git pull origin main
rm -rf dist/ build/
python -m build
```

Before publishing, show the built artifacts (`ls -lh dist/`) and **ask the user to confirm** before running `twine upload`, since PyPI publishes are effectively irreversible.

Check if PyPI auth is available (look for `~/.pypirc` or `TWINE_USERNAME` env var). If auth is not configured, instruct the user to run the upload manually in their own terminal:

```bash
twine upload dist/*
```

### Step 8: Tag the Release

```bash
git tag -a v${VERSION} -m "Release version ${VERSION}"
git push origin v${VERSION}
```

### Step 9: Create GitHub Release

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
- [ ] Preflight: clean working tree
- [ ] Update version in pyproject.toml and derive VERSION from it
- [ ] Create release/${VERSION} branch
- [ ] Regenerate gRPC code if needed (buf generate)
- [ ] Run black, flake8, example imports, pytest
- [ ] Build succeeds (python -m build)
- [ ] Documentation audit (optional, check examples + services in README)
- [ ] Review changes and get user confirmation
- [ ] Commit, push branch, create PR
- [ ] Merge PR to main
- [ ] Clean build, confirm with user, publish to PyPI
- [ ] Create and push git tag (v${VERSION})
- [ ] Create GitHub release
```
