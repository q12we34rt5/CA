#!/bin/sh
# Assemble the course from src/*.html.
#   index.html         standalone page — open this one in a browser
#   dist/artifact.html same content without the <html> wrapper (for publishing as an Artifact)
set -e
cd "$(dirname "$0")"
mkdir -p dist
cat src/[0-9]*.html | python3 -c '
import re, sys
# cap each diagram at ~1.15x its drawn size so small figures are not blown up to full width
def cap(m):
    return "%s style=\"max-width:%dpx\"" % (m.group(0), round(float(m.group(1)) * 1.15))
sys.stdout.write(re.sub(r"viewBox=\"-?\d+ 0 (\d+) \d+\" role=\"img\"", cap, sys.stdin.read()))
' > dist/artifact.html
{
  printf '<!DOCTYPE html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n<body>\n'
  cat dist/artifact.html
  printf '</body>\n</html>\n'
} > index.html
echo "built index.html ($(wc -c < index.html | tr -d ' ') bytes)"
