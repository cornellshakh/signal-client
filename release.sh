#!/bin/bash
set -e

# --- Pre-flight Checks ---
echo "Performing pre-release checks..."

# Check 1: Ensure we are on the main branch
if [[ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]]; then
  echo "Error: Not on the 'main' branch. Please switch to 'main' before releasing."
  exit 1
fi

# Check 2: Ensure the working directory is clean
if ! git diff-index --quiet HEAD --; then
  echo "Error: Uncommitted changes detected. Please commit or stash them before releasing."
  exit 1
fi

# Check 3: Ensure the local branch is in sync with the remote
git fetch origin
if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
  echo "Error: Your local 'main' branch is not in sync with 'origin/main'. Please pull the latest changes."
  exit 1
fi

echo "All checks passed."
echo

# --- Version Bumping ---

# Check if a version bump rule is provided
if [ -z "$1" ] || ! [[ "$1" =~ ^(patch|minor|major)$ ]]; then
  echo "Error: No valid version bump rule provided."
  echo "Usage: ./release.sh <patch|minor|major>"
  exit 1
fi

BUMP_RULE=$1

echo "Bumping version with rule: '$BUMP_RULE'..."
# Use poetry to bump the version and capture the new version number
NEW_VERSION=$(poetry version $BUMP_RULE | awk '{print $3}')
echo "Version updated to $NEW_VERSION in pyproject.toml."
echo

# --- Git Operations ---

# Commit the version change
echo "Committing pyproject.toml..."
git add pyproject.toml
git commit -m "Bump version to $NEW_VERSION"

# Create a git tag
echo "Creating git tag v$NEW_VERSION..."
git tag "v$NEW_VERSION"

# Push the commit and the tag
echo "Pushing commit and tag to origin..."
git push origin main
git push origin "v$NEW_VERSION"

echo
echo "Release v$NEW_VERSION pushed successfully. The GitHub Actions workflow will now handle publishing to PyPI."
