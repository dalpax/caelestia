# NixOS Installation Guide

This guide walks through installing Caelestia on a fresh NixOS system. Because the
upstream `install.fish` script targets Arch Linux and the AUR, NixOS users need to
follow a different path using Nix flakes and Home Manager.

> [!NOTE]
> NixOS Unstable is strongly recommended. Hyprland and several dependencies move
> fast and the unstable channel has the most up-to-date packages.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Enable Flakes](#2-enable-flakes)
3. [Set Up Your Flake](#3-set-up-your-flake)
4. [Configure NixOS (system level)](#4-configure-nixos-system-level)
5. [Configure Home Manager (user level)](#5-configure-home-manager-user-level)
6. [Clone the Dotfiles](#6-clone-the-dotfiles)
7. [Symlink Configs](#7-symlink-configs)
8. [Fix Arch-Specific Paths](#8-fix-arch-specific-paths)
9. [Apply the Configuration](#9-apply-the-configuration)
10. [First Login](#10-first-login)
11. [Optional: Spotify / Spicetify](#11-optional-spotify--spicetify)
12. [Optional: VSCode / VSCodium](#12-optional-vscode--vscodium)
13. [Optional: Zen Browser](#13-optional-zen-browser)
14. [Updating](#14-updating)
15. [Keybinds Reference](#15-keybinds-reference)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Prerequisites

- A working NixOS installation (minimal ISO is fine — no DE needed).
- A non-root user with `sudo` access.
- Internet connectivity.
- `git` available (`nix-shell -p git` if not yet installed).

---

## 2. Enable Flakes

Add the following to `/etc/nixos/configuration.nix` and rebuild before continuing:

```nix
nix.settings.experimental-features = [ "nix-command" "flakes" ];
```

```sh
sudo nixos-rebuild switch
```

---

## 3. Set Up Your Flake

Create a directory for your NixOS configuration (e.g. `~/nixos`) and initialise a
`flake.nix`. Replace `yourhostname` and `yourusername` throughout.

```nix
# ~/nixos/flake.nix
{
  description = "NixOS + Caelestia";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    caelestia-shell = {
      url = "github:caelestia-dots/shell";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, home-manager, caelestia-shell, ... }:
    let
      system = "x86_64-linux";
      pkgs   = nixpkgs.legacyPackages.${system};
    in {
      nixosConfigurations.yourhostname = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          ./configuration.nix
          home-manager.nixosModules.home-manager
          {
            home-manager = {
              useGlobalPkgs = true;
              useUserPackages = true;
              extraSpecialArgs = { inherit caelestia-shell; };
              users.yourusername = import ./home.nix;
            };
          }
        ];
      };
    };
}
```

---

## 4. Configure NixOS (system level)

Create `~/nixos/configuration.nix`. The snippet below covers the services and
packages that Caelestia depends on at the system level.

```nix
# ~/nixos/configuration.nix
{ config, pkgs, lib, ... }:
{
  imports = [ ./hardware-configuration.nix ];

  # ── Boot ──────────────────────────────────────────────────────────────
  boot.loader.systemd-boot.enable      = true;
  boot.loader.efi.canTouchEfiVariables = true;

  # ── Networking ────────────────────────────────────────────────────────
  networking.hostName          = "yourhostname";
  networking.networkmanager.enable = true;

  # ── Locale / Time ─────────────────────────────────────────────────────
  time.timeZone      = "Your/Timezone";
  i18n.defaultLocale = "en_US.UTF-8";

  # ── Users ─────────────────────────────────────────────────────────────
  users.users.yourusername = {
    isNormalUser = true;
    extraGroups  = [ "wheel" "networkmanager" "video" "input" ];
    shell        = pkgs.fish;
  };

  # ── Nix ───────────────────────────────────────────────────────────────
  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  # ── Security / Auth ───────────────────────────────────────────────────
  security.polkit.enable         = true;
  security.rtkit.enable          = true;   # needed by PipeWire
  services.gnome.gnome-keyring.enable = true;

  # ── Audio (PipeWire) ──────────────────────────────────────────────────
  services.pipewire = {
    enable            = true;
    alsa.enable       = true;
    alsa.support32Bit = true;
    pulse.enable      = true;
    wireplumber.enable = true;
  };

  # ── Hyprland ──────────────────────────────────────────────────────────
  programs.hyprland = {
    enable         = true;
    xwayland.enable = true;
  };

  # Required portals for Hyprland (screen share, file picker, etc.)
  xdg.portal = {
    enable = true;
    extraPortals = with pkgs; [
      xdg-desktop-portal-hyprland
      xdg-desktop-portal-gtk
    ];
  };

  # ── UWSM (launches Hyprland as a proper systemd session) ──────────────
  programs.uwsm = {
    enable         = true;
    waylandCompositors.hyprland = {
      prettyName  = "Hyprland";
      comment     = "Hyprland compositor managed by UWSM";
      binPath     = "/run/current-system/sw/bin/Hyprland";
    };
  };

  # ── Login manager (greetd + tuigreet) ─────────────────────────────────
  services.greetd = {
    enable = true;
    settings.default_session = {
      command = "${pkgs.greetd.tuigreet}/bin/tuigreet --time --cmd 'uwsm start hyprland-uwsm.desktop'";
      user    = "greeter";
    };
  };

  # ── Location / Night light ────────────────────────────────────────────
  services.geoclue2.enable = true;

  # ── Bluetooth (optional) ──────────────────────────────────────────────
  # hardware.bluetooth.enable = true;
  # services.blueman.enable   = true;

  # ── DDC/CI brightness (for external monitors) ─────────────────────────
  services.ddccontrol.enable = true;   # or add users to the "i2c" group

  # ── Fonts ─────────────────────────────────────────────────────────────
  fonts = {
    enableDefaultPackages = true;
    packages = with pkgs; [
      nerd-fonts.jetbrains-mono   # Hyprland / terminal
      nerd-fonts.caskaydia-cove   # Caelestia shell UI
      rubik                        # Caelestia shell UI
      material-symbols             # Shell icons (if available in nixpkgs)
    ];
    fontconfig.defaultFonts = {
      monospace = [ "JetBrainsMono Nerd Font" ];
      sansSerif = [ "Rubik" ];
    };
  };

  # ── System packages ───────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    git
    curl
    wget

    # Hyprland ecosystem
    hyprpicker
    wl-clipboard
    cliphist
    inotify-tools
    swappy
    grim
    slurp

    # Qt theming
    libsForQt5.qt5ct
    kdePackages.qt6ct

    # GTK theming
    adw-gtk3
    papirus-icon-theme
    gsettings-desktop-schemas

    # System utilities
    polkit_gnome
    networkmanagerapplet
    brightnessctl
    ddcutil
    lm_sensors
    libnotify

    # Media
    wireplumber    # mpris-proxy
    mpris-proxy    # may be part of wireplumber package

    # Optional: night light
    gammastep
  ];

  # Allow polkit agent to authenticate GUI apps
  systemd.user.services.polkit-gnome-agent = {
    description = "Polkit GNOME Authentication Agent";
    wantedBy    = [ "graphical-session.target" ];
    wants       = [ "graphical-session.target" ];
    after       = [ "graphical-session.target" ];
    serviceConfig = {
      Type      = "simple";
      ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
      Restart   = "on-failure";
    };
  };
}
```

> [!TIP]
> Hardware-specific settings (GPU drivers, CPU microcode, etc.) go in
> `hardware-configuration.nix`, which is generated by `nixos-generate-config`.

---

## 5. Configure Home Manager (user level)

Create `~/nixos/home.nix`. This installs all user-level Caelestia dependencies
and wires up the caelestia-shell Home Manager module.

```nix
# ~/nixos/home.nix
{ config, pkgs, lib, caelestia-shell, ... }:
{
  imports = [ caelestia-shell.homeManagerModules.default ];

  home.username      = "yourusername";
  home.homeDirectory = "/home/yourusername";
  home.stateVersion  = "24.11";   # keep this stable once set

  # ── Caelestia shell + CLI ─────────────────────────────────────────────
  programs.caelestia = {
    enable = true;

    # Start as a systemd user service tied to graphical-session.target.
    # Set enable = false here if you prefer exec-once in hyprland.conf instead.
    systemd = {
      enable = true;
      target = "graphical-session.target";
    };

    settings = {
      # Point at your wallpaper directory
      paths.wallpaperDir = "~/Pictures/Wallpapers";

      # Disable battery indicator if on a desktop
      # bar.status.showBattery = false;
    };

    cli = {
      enable = true;
      settings = {
        # Disable GTK theme application if you manage it yourself
        # theme.enableGtk = false;
      };
    };
  };

  # ── Shell ─────────────────────────────────────────────────────────────
  programs.fish = {
    enable = true;
  };

  programs.starship = {
    enable         = true;
    enableFishIntegration = true;
  };

  programs.direnv = {
    enable               = true;
    nix-direnv.enable    = true;
  };

  programs.zoxide = {
    enable               = true;
    enableFishIntegration = true;
  };

  # ── User packages ─────────────────────────────────────────────────────
  home.packages = with pkgs; [
    # Terminal / shell
    foot
    fastfetch
    btop
    eza
    jq
    trash-cli
    lazygit          # used in fish abbreviations (lg)

    # Wayland utilities
    fuzzel           # emoji / clipboard history picker
    gpu-screen-recorder

    # Audio / media
    cava             # audio visualiser
    aubio            # beat detection
    libqalculate     # calculator (shell widget)
    pavucontrol      # audio control (launched by shell)
    mpv              # media playback

    # Screenshot / screen share
    # (grim, slurp, swappy are in system packages but fine here too)

    # Sass for Discord theming (optional)
    # dart-sass

    # App theming
    nwg-look         # GTK theme switcher (optional, helpful)
  ];

  # Let Home Manager manage itself
  programs.home-manager.enable = true;
}
```

---

## 6. Clone the Dotfiles

> [!WARNING]
> Like on Arch, configs are symlinked — **do not move or delete the repo** after
> running the symlinks in the next step or apps (including Hyprland) will break.

```sh
git clone https://github.com/caelestia-dots/caelestia.git ~/.local/share/caelestia
```

---

## 7. Symlink Configs

The `install.fish` script is Arch-specific, so create the symlinks manually:

```sh
REPO="$HOME/.local/share/caelestia"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"

# Core configs
ln -sf "$REPO/hypr"        "$CFG/hypr"
ln -sf "$REPO/foot"        "$CFG/foot"
ln -sf "$REPO/fish"        "$CFG/fish"
ln -sf "$REPO/fastfetch"   "$CFG/fastfetch"
ln -sf "$REPO/btop"        "$CFG/btop"
ln -sf "$REPO/uwsm"        "$CFG/uwsm"
ln -sf "$REPO/starship.toml" "$CFG/starship.toml"

# Optional: micro editor
ln -sf "$REPO/micro"       "$CFG/micro"
```

If you plan to use VSCodium or VSCode configs, see [Optional: VSCode / VSCodium](#12-optional-vscode--vscodium).

---

## 8. Fix Arch-Specific Paths

Several exec entries in `hypr/hyprland/execs.conf` use hard-coded Arch paths that
do not exist on NixOS. Override them in `~/.config/caelestia/hypr-user.conf`
(which Hyprland sources after the defaults):

```sh
mkdir -p ~/.config/caelestia
```

```conf
# ~/.config/caelestia/hypr-user.conf

# ── Polkit agent ─────────────────────────────────────────────────────────
# The system-level systemd service defined in configuration.nix handles this,
# so no exec-once needed here. If you prefer Hyprland to start it, uncomment:
# exec-once = /run/current-system/sw/bin/polkit-gnome-authentication-agent-1

# ── GeoClue agent ────────────────────────────────────────────────────────
# geoclue2 daemon is managed by systemd. The agent binary path on NixOS:
exec-once = /run/current-system/sw/libexec/geoclue-2.0/demos/agent
```

> [!NOTE]
> The `gnome-keyring-daemon` exec-once works as-is because `gnome-keyring.enable`
> in `configuration.nix` places the daemon on `PATH`. The polkit agent is handled
> by the systemd user service defined earlier, so no extra `exec-once` is needed
> for it.

---

## 9. Apply the Configuration

Copy `hardware-configuration.nix` from `/etc/nixos/` into `~/nixos/`:

```sh
cp /etc/nixos/hardware-configuration.nix ~/nixos/
```

Point NixOS at your new flake and rebuild:

```sh
sudo nixos-rebuild switch --flake ~/nixos#yourhostname
```

This will:
- Install all system and user packages.
- Configure greetd as the login manager.
- Enable Hyprland and the required portals.
- Build and activate the caelestia-shell Home Manager module.

---

## 10. First Login

1. Reboot: `sudo reboot`
2. At the tuigreet prompt, log in — it will automatically start Hyprland via UWSM.
3. Once inside Hyprland, open a terminal with `Super + T`.
4. Set an initial colour scheme:
   ```sh
   caelestia scheme set
   ```
   Follow the prompts to pick a wallpaper and generate the colour palette.
5. Restart the shell to apply colours:
   ```sh
   caelestia shell restart   # or Ctrl+Super+Alt+R
   ```

---

## 11. Optional: Spotify / Spicetify

Install Spotify and Spicetify via Home Manager by adding to `home.nix`:

```nix
# In home.nix
home.packages = with pkgs; [
  spotify
  spicetify-cli
];
```

After rebuilding, symlink the theme and apply:

```sh
ln -sf ~/.local/share/caelestia/spicetify "${XDG_CONFIG_HOME:-$HOME/.config}/spicetify"
spicetify config current_theme caelestia color_scheme caelestia custom_apps marketplace
spicetify apply
```

---

## 12. Optional: VSCode / VSCodium

Add to `home.nix`:

```nix
home.packages = with pkgs; [
  vscodium   # or vscode
];
```

Then symlink the config files (using VSCodium as an example):

```sh
REPO="$HOME/.local/share/caelestia"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"

ln -sf "$REPO/vscode/settings.json"    "$CFG/VSCodium/User/settings.json"
ln -sf "$REPO/vscode/keybindings.json" "$CFG/VSCodium/User/keybindings.json"
ln -sf "$REPO/vscode/flags.conf"       "$CFG/codium-flags.conf"

# Install the Caelestia integration extension
codium --install-extension "$REPO/vscode/caelestia-vscode-integration/caelestia-vscode-integration-"*.vsix
```

Use `code` and `~/.config/Code/User/` for VSCode instead of VSCodium.

---

## 13. Optional: Zen Browser

Zen Browser is not in nixpkgs yet. Install it via a community flake such as
[`youwen5/zen-browser-flake`](https://github.com/youwen5/zen-browser-flake) and
add it as an input, or download and wrap the AppImage manually.

Once installed, symlink the CSS and set up the native app:

```sh
REPO="$HOME/.local/share/caelestia"
PROFILE="<your-zen-profile-id>"   # found inside ~/.zen/

mkdir -p ~/.zen/$PROFILE/chrome
ln -sf "$REPO/zen/userChrome.css" ~/.zen/$PROFILE/chrome/userChrome.css

# Native messaging host
mkdir -p ~/.mozilla/native-messaging-hosts
mkdir -p ~/.local/lib/caelestia

LIB_PATH="$HOME/.local/lib/caelestia"
sed "s|{{ \$lib }}|$LIB_PATH|g" \
    "$REPO/zen/native_app/manifest.json" \
    > ~/.mozilla/native-messaging-hosts/caelestiafox.json

ln -sf "$REPO/zen/native_app/app.fish" "$LIB_PATH/caelestiafox"
chmod +x "$LIB_PATH/caelestiafox"
```

Then install the [CaelestiaFox extension](https://addons.mozilla.org/en-US/firefox/addon/caelestiafox)
from the Firefox Add-ons site inside Zen Browser.

---

## 14. Updating

**NixOS / packages:**

```sh
nix flake update ~/nixos
sudo nixos-rebuild switch --flake ~/nixos#yourhostname
```

**Dotfiles:**

```sh
cd ~/.local/share/caelestia
git pull
```

**Caelestia shell** is pinned to the flake lock. To update it along with nixpkgs:

```sh
nix flake update ~/nixos   # updates all inputs including caelestia-shell
sudo nixos-rebuild switch --flake ~/nixos#yourhostname
```

---

## 15. Keybinds Reference

| Keys | Action |
|------|--------|
| `Super` | Open launcher |
| `Super` + `1-9` | Switch workspace |
| `Super Alt` + `1-9` | Move window to workspace |
| `Super` + `T` | Terminal (foot) |
| `Super` + `W` | Browser (Zen) |
| `Super` + `C` | Editor (VSCodium) |
| `Super` + `E` | File manager (Thunar) |
| `Super` + `S` | Toggle special workspace |
| `Ctrl Alt` + `Delete` | Session menu |
| `Super` + `L` | Lock screen |
| `Ctrl Super` + `Space` | Toggle media play |
| `Ctrl Super Alt` + `R` | Restart shell |

---

## 16. Troubleshooting

**Hyprland fails to start / black screen**
- Check `journalctl --user -xe` for errors.
- Confirm `programs.hyprland.enable = true` is in `configuration.nix`.
- Ensure the GPU driver is correctly set up in `hardware-configuration.nix`.

**Shell (quickshell) does not appear**
- Verify `programs.caelestia.enable = true` in `home.nix` and that the rebuild succeeded.
- Run `caelestia shell -d` manually in a foot terminal to see debug output.
- If using `systemd.enable = true` in the caelestia module, check
  `systemctl --user status caelestia-shell`.

**No colour scheme / theming looks wrong**
- Run `caelestia scheme set` from a terminal to generate `hypr/scheme/current.conf`.
- Make sure a wallpaper directory is set in `programs.caelestia.settings.paths.wallpaperDir`.

**polkit / authentication dialogs do not appear**
- Verify the systemd user service `polkit-gnome-agent` is active:
  `systemctl --user status polkit-gnome-agent`.

**`/usr/lib/geoclue-2.0/demos/agent` not found**
- Confirm the override in `~/.config/caelestia/hypr-user.conf` points to the
  NixOS path (`/run/current-system/sw/libexec/geoclue-2.0/demos/agent`).
- Alternatively disable the exec-once entirely; geoclue2 runs as a system daemon.

**Qt apps look unstyled**
- Make sure `QT_QPA_PLATFORMTHEME=qt6ct` is set (it is in `hypr/hyprland/env.conf`)
  and that `libsForQt5.qt5ct` / `kdePackages.qt6ct` are installed.
- Open `qt6ct` from a terminal to configure the theme manually.

**`app2unit` not found**
- `app2unit` is not currently packaged in nixpkgs. Caelestia uses it for launching
  apps as transient systemd units. UWSM already provides similar scope management
  for the session itself. If the caelestia CLI complains about a missing `app2unit`,
  you can build it from source:
  ```sh
  nix shell "github:Vladimir-csp/app2unit"
  ```
  Or add it to your flake as an input until an official nixpkg is available.
