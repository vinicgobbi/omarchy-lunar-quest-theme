-- Earthrise over the limb: ocean blue fading into lunar highlight.
local active_border_color = { colors = { "rgba(7ea3cfee)", "rgba(c3c0c0ee)" }, angle = 45 }
local inactive_border_color = "rgba(223855aa)"

-- Earthshine: the focused window carries a soft blue glow, the way sunlight
-- reflected off Earth lights the night side of the Moon.
local active_shadow_color = "rgba(7ea3cf55)"
local inactive_shadow_color = "rgba(04070e66)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },

  decoration = {
    shadow = {
      enabled = true,
      range = 14,
      render_power = 3,
      color = active_shadow_color,
      color_inactive = inactive_shadow_color,
    },
  },
})
