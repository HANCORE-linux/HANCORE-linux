#!/usr/bin/env bash
# Compatibility entry point for the current publication build.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python "$root/scripts/build_profile.py" "$@"
