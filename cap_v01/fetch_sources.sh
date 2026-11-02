#!/usr/bin/env bash
# Local convenience: fetch the pinned CAP v0.1 G1 sources by exact SHA into <destination-dir>/<dir> and verify HEAD. The hosted workflow uses actions/checkout instead.
# The Control Plane is fetched WITH FULL HISTORY of main (the tripwire diffs the head against the base commit); Registry and Replay are fetched by SHA.
# usage: fetch_sources.sh <destination-dir>      (no secrets, public repositories only)
set -euo pipefail
dest="${1:?destination directory}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$dest"
python3 - "$here/sources.json" > "$dest/.pins.tsv" <<'PY'
import json, sys
for name, s in json.load(open(sys.argv[1]))["sources"].items():
    if s.get("dir"):
        print("\t".join([name, s["repo"], s["sha"], s["dir"], s.get("branch") or "-"]))
PY
while IFS=$'\t' read -r name repo sha dir branch; do
  d="$dest/$dir"
  rm -rf "$d"; mkdir -p "$d"
  git -C "$d" init -q
  if [ "$branch" != "-" ]; then
    git -C "$d" fetch -q "https://github.com/cogno-us/$repo" "+refs/heads/$branch:refs/remotes/origin/$branch" </dev/null
  else
    git -C "$d" fetch -q --depth 1 "https://github.com/cogno-us/$repo" "$sha" </dev/null
  fi
  git -C "$d" checkout -q --detach "$sha"
  head="$(git -C "$d" rev-parse HEAD)"
  if [ "$head" != "$sha" ]; then
    echo "::error::$name pin mismatch: HEAD $head (want $sha)"; exit 1
  fi
  printf '%s\t%s\t%s\n' "$name" "$repo" "$head"
done < "$dest/.pins.tsv"
