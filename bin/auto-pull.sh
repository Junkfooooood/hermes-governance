#!/bin/bash
# Auto-pull script for Hermes project evolution
cd "$HOME/.hermes" || exit 1

# Only fast-forward to avoid merge conflicts with local changes
git fetch origin main 2>/dev/null
git merge --ff-only origin/main 2>/dev/null
