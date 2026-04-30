#!/usr/bin/env bash
# bump-version.sh — Update version across all project manifests and optionally create a git tag.
#
# Usage:
#   ./scripts/bump-version.sh 0.2.0          # bump files only
#   ./scripts/bump-version.sh 0.2.0 --tag    # bump files, commit, and create git tag v0.2.0
#
# Files updated:
#   - aipresence/config.yaml          (HA add-on manifest)
#   - custom_components/aipresence/manifest.json  (HA integration manifest)
#   - aipresence/client/package.json   (frontend)

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <version> [--tag]"
  echo "  e.g. $0 0.2.0 --tag"
  exit 1
fi

VERSION="$1"
CREATE_TAG=false
if [[ "${2:-}" == "--tag" ]]; then
  CREATE_TAG=true
fi

# Validate semver-ish format (digits.digits.digits with optional pre-release suffix)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
  echo "Error: Version '$VERSION' doesn't look like semver (expected X.Y.Z or X.Y.Z-suffix)"
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "Bumping version to $VERSION ..."

# 1. aipresence/config.yaml
sed -i "s/^version: .*/version: \"$VERSION\"/" "$REPO_ROOT/aipresence/config.yaml"
echo "  ✓ aipresence/config.yaml"

# 2. custom_components/aipresence/manifest.json
sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$REPO_ROOT/custom_components/aipresence/manifest.json"
echo "  ✓ custom_components/aipresence/manifest.json"

# 3. aipresence/client/package.json (only the top-level "version" field)
sed -i "0,/\"version\": \"[^\"]*\"/{s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/}" "$REPO_ROOT/aipresence/client/package.json"
echo "  ✓ aipresence/client/package.json"

echo ""
echo "All files bumped to $VERSION"

if $CREATE_TAG; then
  echo ""
  echo "Creating git commit and tag..."
  git add \
    "$REPO_ROOT/aipresence/config.yaml" \
    "$REPO_ROOT/custom_components/aipresence/manifest.json" \
    "$REPO_ROOT/aipresence/client/package.json"
  git commit -m "release: v$VERSION"
  git tag "v$VERSION"
  echo ""
  echo "Done. Push with:"
  echo "  git push && git push --tags"
fi
