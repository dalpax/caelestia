-- Personal Hyprland config, loaded last (after all caelestia configs).
-- Ported from the old hyprland.conf / input.conf / keybinds.conf customisations.

-- Monitors
hl.monitor({ output = "HDMI-A-1", mode = "preferred", position = "auto", scale = 1 })
hl.monitor({ output = "eDP-1", mode = "1920x1080@60.00Hz", position = "auto", scale = 1 })

-- Input: flat mouse acceleration
hl.config({
    input = {
        accel_profile = "flat",
    },
})

-- Per-device sensitivity (find names with `hyprctl devices`)
hl.device({ name = "razer-razer-deathadder-v2", sensitivity = 0 })
hl.device({ name = "msi-msi-gm20-elite-", sensitivity = -0.2 })
hl.device({ name = "asue120a:00-04f3:319b-touchpad", sensitivity = 0.6 })
hl.device({ name = "logitech-usb-trackball", sensitivity = 1.0 }) -- libinput max is 1.0

-- Lid close: blank internal panel only (VM + session keep running). Restore on open.
hl.bind("switch:on:Lid Switch", hl.dsp.exec_cmd("hyprctl dispatch dpms off eDP-1"), { locked = true })
hl.bind("switch:off:Lid Switch", hl.dsp.exec_cmd("hyprctl dispatch dpms on eDP-1"), { locked = true })

-- Counter-Strike 2 (native Linux build reports class "cs2", so it misses
-- upstream's steam_app_* game-tag patterns). The "game" tag is defined in
-- hypr/hyprland/rules.lua: opaque + immediate + idle_inhibit.
hl.window_rule({ match = { class = "cs2" }, tag = "+game" })
