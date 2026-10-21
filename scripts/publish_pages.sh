#!/usr/bin/env bash
# Rebuild the console and publish it to the gh-pages branch (GitHub Pages).
# Needs the data pack in data/. Run from the repo root.
set -euo pipefail
python scoring/score.py >/dev/null
python scoring/export_points.py
python scoring/export_map.py
python app/build.py
tmp=$(mktemp -d)
cp out/site/index.html out/site/.nojekyll out/site/llms.txt "$tmp"/
cd "$tmp"
git init -q -b gh-pages
git add -A
git commit -qm "Publish AquaSentinel console"
git push -f "$(git -C "$OLDPWD" remote get-url origin)" HEAD:gh-pages
echo "Published: https://starwaterheaven.github.io/AquaSentinel/"
