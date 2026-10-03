# Compatibility

Lunar Quest targets **Omarchy 4 (Quattro)**: its Quickshell interface
(`shell.toml`) and Lua Hyprland configuration (`hyprland.lua`). Omarchy 3 and
older use a different shell stack and Hyprland config format and are not
supported.

| Omarchy version | Status |
|---|---|
| 4.0.4-1 | Tested |
| Newer 4.x | Not tested |

A newer Omarchy only breaks this theme if it renames or repurposes a token
`shell.toml` sets, or changes the `hl.config` keys `hyprland.lua` uses. New
optional tokens fall back to Omarchy's defaults.

If something breaks, please open an issue with your `omarchy version` output.
