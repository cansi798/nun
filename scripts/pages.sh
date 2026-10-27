#!/bin/bash
# Baut die Fassung für GitHub Pages nach site/ (Basis /nun/site/).
set -e
cd "$(dirname "$0")/.."
rm -rf site
npm run build:pages
touch site/.nojekyll
