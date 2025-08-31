# VRChat Join Notification (Linux)

A simple log-watcher that notifies you when someone joins your current VRChat world.  
No unofficial API calls – it only reads your **local VRChat logs** (safe and ToS-friendly).

![screenshot](https://raw.githubusercontent.com/yueplush/vrchat-join-notification/refs/heads/main/notify.png)  
*(example notification on GNOME desktop)*

---

# Features
- ToS-safe: no API keys, only local logs
- Desktop notification via `notify-send`
- Auto-switches to the latest VRChat log after restart
- Optional: custom icon or sound
- Quick installer (`install.sh`) with distro detection (Debian/Ubuntu, Fedora/Bazzite, Arch/Manjaro)

---
## depency
python 3.13 or higher

---

# Install (One-liner)

```bash
git clone https://github.com/yueplush/vrchat-join-notification.git
cd vrchat-join-notification
chmod +x installsh
bash ./install.sh
```

This will:
Install dependencies (libnotify) if supported
Copy the script to ~/.local/bin/vrc_join_notify.py
Register and start the systemd user service vrc-join-notify.service

# uninstall

```bash
cd vrchat-join-notification
chmod +x uninsatll.sh
bash ./uninstall.sh
```

# Manual Setup

## Install dependency
Ubuntu/Debian: sudo apt install libnotify-bin
Fedora/Bazzite: sudo dnf install libnotify
Arch/Manjaro: sudo pacman -S libnotify

## Place script
mkdir -p ~/.local/bin
cp vrc_join_notify.py ~/.local/bin/
chmod +x ~/.local/bin/vrc_join_notify.py

## Place systemd service
mkdir -p ~/.config/systemd/user
cp vrc-join-notify.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now vrc-join-notify.service

Configuration
Open the top of vrc_join_notify.py and edit:

TITLE = "VRChat"
ICON = "/path/to/icon.png"   # Optional
SOUND = "/usr/share/sounds/freedesktop/stereo/message.oga"  # Optional

Change ICON to use a custom PNG in notifications
Change SOUND to play a sound using paplayDevelopment

Works on Linux + Steam/Proton and Flatpak Steam

Watches log files under:
~/.local/share/Steam/steamapps/compatdata/438100/.../VRChat/VRChat
~/.var/app/com.valvesoftware.Steam/.../VRChat/VRChat
~/.config/unity3d/VRChat/VRChat

License
MIT




