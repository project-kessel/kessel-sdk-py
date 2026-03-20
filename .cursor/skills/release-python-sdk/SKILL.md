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

Edit `pyproject.toml` and set the new version:

```bash
# Set the target version
export VERSION="X.Y.Z"
```

Then update the `version` field in `pyproject.toml` to match `$VERSION`.

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: incompatible API changes
- **MINOR**: backward-compatible new functionality
- **PATCH**: backward-compatible bug fixes

Verify the update:

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

### Step 4: Commit and Push

```bash
git add pyproject.toml
git commit -m "Release version ${VERSION}"
git push origin main
```

Include any other changed files (generated code, lock files) in the commit.

### Step 5: Build and Publish to PyPI

```bash
rm -rf dist/ build/
python -m build
twine upload dist/*
```

### Step 6: Tag the Release

```bash
git tag -a v${VERSION} -m "Release version ${VERSION}"
git push origin v${VERSION}
```

### Step 7: Create GitHub Release

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
- [ ] Set VERSION and update pyproject.toml
- [ ] Regenerate gRPC code if needed (buf generate)
- [ ] Run black, flake8, example imports, pytest
- [ ] Build succeeds (python -m build)
- [ ] Commit and push version bump
- [ ] Clean build and publish to PyPI (twine upload dist/*)
- [ ] Create and push git tag (v${VERSION})
- [ ] Create GitHub release
```
