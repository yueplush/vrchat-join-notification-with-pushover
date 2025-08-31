#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_SRC="${REPO_DIR}/vrc_join_notify.py"
SERVICE_SRC="${REPO_DIR}/vrc-join-notify.service"

BIN_DIR="${HOME}/.local/bin"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"

INSTALL_DEPS=1
START_SERVICE=1
ENABLE_LINGER=0

usage() {
  cat <<'USAGE'
VRChat Join Notifier installer
Usage: ./install.sh [--no-deps] [--no-start] [--linger]

  --no-deps   Skip installing system dependencies (libnotify/notify-send)
  --no-start  Do not enable/start the systemd user service
  --linger    Run 'loginctl enable-linger $USER' to keep user services running without active login
USAGE
}

# --- parse args (no phantom empty-arg bug) ---
for arg in "$@"; do
  case "$arg" in
    --no-deps)  INSTALL_DEPS=0 ;;
    --no-start) START_SERVICE=0 ;;
    --linger)   ENABLE_LINGER=1 ;;
    -h|--help)  usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

# --- sanity checks ---
if [[ ! -f "$SCRIPT_SRC" || ! -f "$SERVICE_SRC" ]]; then
  echo "Error: vrc_join_notify.py or vrc-join-notify.service not found next to install.sh" >&2
  exit 1
fi

detect_distro_and_install() {
  if [[ "$INSTALL_DEPS" -eq 0 ]]; then
    echo "[info] Skipping dependency install (--no-deps)."
    return
  fi

  local DISTRO="unknown"
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    DISTRO="${ID:-unknown}"
  else
    echo "[warn] /etc/os-release not found. Skipping dependency install."
    return
  fi
  echo "[info] Detected distro: ${DISTRO}"

  case "$DISTRO" in
    ubuntu|debian)
      sudo apt update
      sudo apt install -y libnotify-bin
      ;;
    fedora|rhel|centos|nobara|bazzite)
      sudo dnf install -y libnotify
      ;;
    arch|manjaro|endeavouros|garuda)
      sudo pacman -Sy --noconfirm libnotify
      ;;
    *)
      echo "[warn] Unsupported distro '$DISTRO'. Please install 'notify-send' (libnotify) manually."
      ;;
  esac

  if ! command -v notify-send >/dev/null 2>&1; then
    echo "[warn] 'notify-send' not found in PATH. Make sure libnotify is installed correctly." >&2
  fi
}

place_files() {
  mkdir -p "$BIN_DIR" "$SYSTEMD_USER_DIR"
  install -m 0755 "$SCRIPT_SRC" "$BIN_DIR/vrc_join_notify.py"
  install -m 0644 "$SERVICE_SRC" "$SYSTEMD_USER_DIR/vrc-join-notify.service"
  echo "[ok] Installed:"
  echo " - $BIN_DIR/vrc_join_notify.py"
  echo " - $SYSTEMD_USER_DIR/vrc-join-notify.service"
}

enable_linger_if_requested() {
  if [[ "$ENABLE_LINGER" -eq 1 ]]; then
    if command -v loginctl >/dev/null 2>&1; then
      echo "[info] Enabling linger for $USER (keeps user services running without active login)"
      sudo loginctl enable-linger "$USER" || true
    else
      echo "[warn] loginctl not found; cannot enable linger."
    fi
  fi
}

start_service() {
  if [[ "$START_SERVICE" -eq 0 ]]; then
    echo "[info] Not starting service (--no-start)."
    return
  fi

  if ! command -v systemctl >/dev/null 2>&1; then
    echo "[warn] systemctl not found. Skipping service start. You can run the script directly:"
    echo "      $BIN_DIR/vrc_join_notify.py"
    return
  fi

  systemctl --user daemon-reload
  systemctl --user enable --now vrc-join-notify.service
  echo "[ok] Service enabled and started: vrc-join-notify.service"

  echo
  echo "Tips:"
  echo "  - Check status:   systemctl --user status vrc-join-notify.service"
  echo "  - View logs:      journalctl --user -u vrc-join-notify.service -f"
}

main() {
  detect_distro_and_install
  place_files
  enable_linger_if_requested
  start_service
  echo
  echo "[done] VRChat Join Notifier is installed."
}

main "$@"

