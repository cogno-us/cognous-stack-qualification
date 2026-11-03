#!/usr/bin/env bash
# Fetch every pinned source of sources.json (PRIVATE PREVIEW QUALIFICATION TUPLE) by exact SHA
# (git init + git fetch --depth 1 <https url> <sha> + checkout --detach) and verify HEAD and tree.
# Fails if a work tree is dirty / has untracked or ignored files, or has an interpreter-startup or shadow-module file at a source root.
# usage: fetch_sources.sh <destination-dir>      (no secrets, public repositories only; needs network access to github.com)
# stdout: TSV  name<TAB>repo<TAB>sha<TAB>tree
set -euo pipefail
dest="${1:?destination directory}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$dest"
python3 - "$here/sources.json" > "$dest/.pins.tsv" <<'PY'
import json, sys
for name, s in json.load(open(sys.argv[1]))["sources"].items():
    print("\t".join([name, s["repo"], s["sha"], s["tree"], s["dir"]]))
PY
while IFS=$'\t' read -r name repo sha tree dir; do
  d="$dest/$dir"
  rm -rf "$d"; mkdir -p "$d"
  git -C "$d" init -q
  git -C "$d" fetch -q --depth 1 "https://github.com/cogno-us/$repo" "$sha" </dev/null
  git -C "$d" checkout -q --detach FETCH_HEAD
  head="$(git -C "$d" rev-parse HEAD)"; gtree="$(git -C "$d" rev-parse 'HEAD^{tree}')"
  if [ "$head" != "$sha" ] || [ "$gtree" != "$tree" ]; then
    echo "::error::$name pin mismatch: HEAD $head (want $sha) tree $gtree (want $tree)" >&2; exit 1
  fi
  dirty="$(git --no-replace-objects -C "$d" status --porcelain --untracked-files=all --ignored)"
  if [ -n "$dirty" ]; then
    echo "::error::$name work tree is not clean after checkout:" >&2; echo "$dirty" >&2; exit 1
  fi
  shadow="$(find "$d" -maxdepth 3 \( -name '*.pth' -o -name 'sitecustomize.py' -o -name 'usercustomize.py' -o -name 'sitecustomize' -o -name 'usercustomize' \) -not -path '*/.git/*' || true)"
  if [ -n "$shadow" ]; then
    echo "::error::$name contains interpreter-startup/shadow files:" >&2; echo "$shadow" >&2; exit 1
  fi
  printf '%s\t%s\t%s\t%s\n' "$name" "$repo" "$head" "$gtree"
done < "$dest/.pins.tsv"
rm -f "$dest/.pins.tsv"
