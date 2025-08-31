#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"

systemctl --user disable --now vrc-join-notify.service || true
systemctl --user daemon-reload || true
rm -f "${SYSTEMD_USER_DIR}/vrc-join-notify.service"
rm -f "${BIN_DIR}/vrc_join_notify.py"
echo "[ok] Uninstalled VRChat Join Notifier."

