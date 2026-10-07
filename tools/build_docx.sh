#!/usr/bin/env bash
# Converts docs/md/*.md to docs/docx/*.docx (upload the .docx files to SharePoint).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p docs/docx
for f in docs/md/DOC-*.md; do
  pandoc "$f" -f markdown -t docx -o "docs/docx/$(basename "${f%.md}").docx"
done
echo "Built $(ls docs/docx/*.docx | wc -l) files in docs/docx/"
