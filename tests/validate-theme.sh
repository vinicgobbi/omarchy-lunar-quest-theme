#!/usr/bin/env bash
# Validate the Lunar Quest theme package: palette and shell tokens, the files
# that repeat palette colors, image sizes, and that the generated art matches
# art/generate.py.
#
#   bash tests/validate-theme.sh
#
# Needs python3 (3.11+ for tomllib), ImageMagick (6 or 7), rsvg-convert and git.

set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

failures=0
fail() {
  echo "FAIL: $*" >&2
  failures=$((failures + 1))
}
pass() {
  echo "ok:   $*"
}

# ImageMagick 7 ships `magick <tool>`; Ubuntu still ships IM6's bare tools.
im() {
  if command -v magick >/dev/null 2>&1; then
    magick "$@"
  else
    "$@"
  fi
}

# --- Palette, shell and repeated colors ------------------------------------

if python3 - <<'EOF'
import re
import sys
import tomllib

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
RGBA = re.compile(r"rgba?\(([0-9a-fA-F]{6})(?:[0-9a-fA-F]{2})?\)")
errors = []

colors = tomllib.load(open("colors.toml", "rb"))
required = """accent selection muted background dark_background darker_background
lighter_background foreground dark_foreground light_foreground bright_foreground
red yellow orange green cyan blue magenta brown bright_red bright_yellow
bright_green bright_cyan bright_blue bright_magenta""".split()

if colors.get("mode") != "dark":
    errors.append('colors.toml: mode must be "dark"')
for key in required:
    value = colors.get(key)
    if value is None:
        errors.append(f"colors.toml: missing {key}")
    elif not HEX.match(value):
        errors.append(f"colors.toml: {key} = {value!r} is not #rrggbb")

border = colors.get("hyprland_active_border", "")
border_colors = [c.lower() for c in RGBA.findall(border)]
if len(border_colors) < 2:
    errors.append("colors.toml: hyprland_active_border needs a two-color gradient")

shell = tomllib.load(open("shell.toml", "rb"))
for section, values in shell.items():
    for key, value in values.items():
        if isinstance(value, str) and value.startswith("#") and not HEX.match(value):
            errors.append(f"shell.toml: [{section}] {key} = {value!r} is not #rrggbb")
        if key.endswith("alpha") and not 0 <= value <= 1:
            errors.append(f"shell.toml: [{section}] {key} = {value} is outside 0..1")

# hyprland.lua and shell.toml [hyprland] replace generated files, so they must
# repeat the border gradient colors.toml declares.
shell_border = shell.get("hyprland", {}).get("active-border", "")
if [c.lower() for c in RGBA.findall(shell_border)] != border_colors:
    errors.append("shell.toml: [hyprland] active-border differs from colors.toml")
lua = open("hyprland.lua").read().lower()
for color in border_colors:
    if color not in lua:
        errors.append(f"hyprland.lua: border color {color} from colors.toml is missing")

btop_keys = 0
for line in open("btop.theme"):
    match = re.match(r'^theme\[(\w+)\]="(.*)"$', line.strip())
    if not match:
        continue
    btop_keys += 1
    if match.group(2) and not HEX.match(match.group(2)):
        errors.append(f"btop.theme: {match.group(1)} = {match.group(2)!r} is not #rrggbb")
if btop_keys < 40:
    errors.append(f"btop.theme: only {btop_keys} theme[] entries")

icons = open("icons.theme").read().strip()
if not re.match(r"^[\w.+-]+$", icons):
    errors.append(f"icons.theme: {icons!r} is not a single icon theme name")

for error in errors:
    print(f"FAIL: {error}", file=sys.stderr)
sys.exit(1 if errors else 0)
EOF
then
  pass "colors.toml, shell.toml, hyprland.lua, btop.theme, icons.theme"
else
  failures=$((failures + 1))
fi

# --- Images -----------------------------------------------------------------

expect_size() {
  local file=$1 expected=$2 actual

  if [[ ! -f $file ]]; then
    fail "$file is missing"
    return
  fi
  actual=$(im identify -format '%wx%h' "$file")
  if [[ $actual == "$expected" ]]; then
    pass "$file is $expected"
  else
    fail "$file is $actual, expected $expected"
  fi
}

expect_size backgrounds/0-omarchy-lunar-quest.png 3840x2160
expect_size backgrounds/omarchy.png 3840x2160
expect_size preview.png 1800x1012
expect_size preview-unlock.png 1920x1080

unlock_width=$(im identify -format '%w' unlock.png)
unlock_alpha=$(im identify -format '%A' unlock.png)
if [[ $unlock_width == 800 && $unlock_alpha =~ ^([Tt]rue|[Bb]lend)$ ]]; then
  pass "unlock.png is 800px wide with transparency"
else
  fail "unlock.png must be 800px wide with transparency (got ${unlock_width}px, alpha $unlock_alpha)"
fi

photos=(backgrounds/[1-9]-*.jpg)
if (( ${#photos[@]} == 6 )); then
  pass "six photo backgrounds"
else
  fail "expected six photo backgrounds, found ${#photos[@]}"
fi
for photo in "${photos[@]}"; do
  width=$(im identify -format '%w' "$photo")
  (( width >= 1920 )) || fail "$photo is only ${width}px wide"
done

# --- Generated art ------------------------------------------------------------

# Regenerate, then require identical SVGs and pixel-identical PNGs. PNG bytes
# may differ between librsvg builds, so PNGs are compared by pixels.
generated_pngs=(backgrounds/0-omarchy-lunar-quest.png backgrounds/omarchy.png preview.png unlock.png)
committed=$(mktemp -d)
trap 'rm -rf "$committed"' EXIT
for png in "${generated_pngs[@]}"; do
  mkdir -p "$committed/$(dirname "$png")"
  cp "$png" "$committed/$png"
done

python3 art/generate.py >/dev/null

if git diff --quiet -- 'art/*.svg'; then
  pass "art/*.svg match art/generate.py"
else
  fail "art/*.svg are out of date; run python3 art/generate.py and commit"
  git --no-pager diff --stat -- 'art/*.svg' >&2
fi

for png in "${generated_pngs[@]}"; do
  if differing=$(im compare -metric AE "$committed/$png" "$png" null: 2>&1) && [[ ${differing%% *} == 0 ]]; then
    pass "$png matches art/generate.py"
  else
    fail "$png differs from art/generate.py output ($differing pixels)"
  fi
done

# ----------------------------------------------------------------------------

if (( failures > 0 )); then
  echo "$failures check(s) failed" >&2
  exit 1
fi
echo "All checks passed"
