#!/bin/sh
# Render every <figure> of one chapter file to its own PNG so the drawing can be checked by eye.
#   tools/figshot.sh src/20-datapath.html [dark]
# Output: /tmp-like scratch dir printed at the end (one PNG per figure, in document order).
set -e
cd "$(dirname "$0")/.."
src="$1"; theme="${2:-light}"
name="$(basename "$src" .html)"
out="${FIGSHOT_OUT:-.figshot}/$name"
rm -rf "$out"; mkdir -p "$out"
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
prof="$(mktemp -d)"; trap 'rm -rf "$prof"' EXIT   # own profile so parallel runs do not collide
n=$(grep -c '<figure' "$src" || true)
i=0
while [ "$i" -lt "$n" ]; do
  page="$out/fig-$i.html"
  {
    printf '<!DOCTYPE html><html lang="zh-Hant" data-theme="%s"><head><meta charset="utf-8"></head><body>\n' "$theme"
    cat src/00-head.html "$src" src/99-tail.html
    printf '<script>(function(){var f=document.querySelectorAll("main figure")[%d];var keep=Array.prototype.slice.call(document.querySelectorAll("body>style,body>svg"));document.body.replaceChildren.apply(document.body,keep.concat([f]));document.body.style.padding="12px";f.style.maxWidth="900px";})();</script></body></html>\n' "$i"
  } > "$page"
  # with a private profile Chrome may not exit after the screenshot: wait for the PNG, then stop it
  "$chrome" --headless=new --user-data-dir="$prof" --no-first-run --disable-gpu --hide-scrollbars \
    --window-size=940,640 --screenshot="$PWD/$out/fig-$i.png" "file://$PWD/$page" >/dev/null 2>&1 &
  pid=$!; t=0
  while [ ! -s "$out/fig-$i.png" ] && [ "$t" -lt 100 ]; do sleep 0.2; t=$((t+1)); done
  sleep 0.3; kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true
  rm -f "$page"
  i=$((i+1))
done
echo "$n figure(s) -> $PWD/$out"
