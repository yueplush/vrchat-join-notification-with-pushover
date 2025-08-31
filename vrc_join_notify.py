#!/usr/bin/env python3
# VRChat Join Notifier (Linux) — self join filter
import time, os, re, sys, subprocess
from pathlib import Path
import json
from urllib.request import Request, urlopen
from urllib.error import URLError

TITLE = "VRChat"
ICON = None
SOUND = None

JOIN_PATTERNS = [
    re.compile(r"OnPlayerJoined", re.IGNORECASE),
    re.compile(r"\bplayer\s+joined\b", re.IGNORECASE),
]
EXTRACT_PATTERNS = [
    re.compile(r"OnPlayerJoined.*?\s([^\]\)\}]+)$", re.IGNORECASE),
    re.compile(r'displayName"\s*:\s*"([^"]+)"', re.IGNORECASE),
]

# --- try to detect "self" display name from log noise ---
SELF_PATTERNS = [
    re.compile(r'displayName"\s*:\s*"([^"]+)"\s*,\s*"id"\s*:\s*"\w+"\s*,\s*"isFriend"\s*:\s*false.*?"currentUser":\s*{', re.I),
    re.compile(r'APIUser[^}]*displayName"\s*:\s*"([^"]+)"', re.I),
    re.compile(r'Authenticated\s+as\s+([^\r\n]+)', re.I),
    re.compile(r'Local\s+user\s*:\s*([^\r\n]+)', re.I),
]

HOME = Path.home()
CANDIDATE_DIRS = [
    HOME / ".local/share/Steam/steamapps/compatdata/438100/pfx/drive_c/users/steamuser/AppData/LocalLow/VRChat/VRChat",
    HOME / ".steam/steam/steamapps/compatdata/438100/pfx/drive_c/users/steamuser/AppData/LocalLow/VRChat/VRChat",
    HOME / ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/438100/pfx/drive_c/users/steamuser/AppData/LocalLow/VRChat/VRChat",
    HOME / ".config/unity3d/VRChat/VRChat",
]
LOG_GLOBS = ["output_log_*.txt", "Player.log", "output_log.txt"]

def find_latest_log():
    latest, latest_mtime = None, -1
    for d in CANDIDATE_DIRS:
        if not d.exists():
            continue
        for pattern in LOG_GLOBS:
            for p in d.glob(pattern):
                try:
                    m = p.stat().st_mtime
                    if m > latest_mtime:
                        latest_mtime, latest = m, p
                except FileNotFoundError:
                    pass
    return latest

def push_pushover(title: str, body: str):
    token = os.environ.get("PUSHOVER_TOKEN", "")
    user  = os.environ.get("PUSHOVER_USER", "")
    if not (token and user):
        return
    # application/x-www-form-urlencoded で送る（requests不要）
    payload = f"token={token}&user={user}&title={title}&message={body}".encode("utf-8")
    req = Request(
        "https://api.pushover.net/1/messages.json",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        urlopen(req, timeout=3).read()
    except URLError as e:
        print(f"[warn] pushover failed: {e}", file=sys.stderr)

def notify(body: str):
    args = ["notify-send", TITLE, body, "-u", "normal"]
    if ICON: args.extend(["-i", ICON])
    try:
        subprocess.run(args, check=False)
    except Exception as e:
        print(f"[warn] notify-send failed: {e}", file=sys.stderr)
    if SOUND:
        try: subprocess.run(["paplay", SOUND], check=False)
        except Exception as e: print(f"[warn] paplay failed: {e}", file=sys.stderr)

    # Pushoverへも送る
    push_pushover(TITLE, body)

def extract_name(line: str) -> str:
    for rx in EXTRACT_PATTERNS:
        m = rx.search(line)
        if m:
            return m.group(1).strip().strip("[]{}()<>\"' ")
    return ""

def detect_self_name(path: Path, override_cli: str | None) -> str:
    if override_cli:   # --self "NAME"
        return override_cli.strip()
    env = os.environ.get("VRC_SELF_NAME", "").strip()
    if env:
        return env
    # best-effort: scan recent tail of file for a likely "self" name
    try:
        with open(path, "r", errors="ignore", encoding="utf-8", newline="") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 200_000))  # last ~200KB
            chunk = f.read()
        for rx in SELF_PATTERNS:
            m = rx.search(chunk)
            if m:
                return m.group(1).strip().strip("[]{}()<>\"' ")
    except Exception:
        pass
    return ""  # unknown

def tail_f(path: Path, self_name: str):
    print(f"[info] Following: {path}")
    if self_name:
        print(f"[info] Self name filter: '{self_name}' (case-insensitive)")
    f = open(path, "r", errors="ignore", encoding="utf-8", newline="")
    f.seek(0, os.SEEK_END)
    last_check = time.time()

    def is_self(n: str) -> bool:
        return bool(self_name) and n.lower() == self_name.lower()

    while True:
        line = f.readline()
        if not line:
            if time.time() - last_check > 5:
                last_check = time.time()
                latest = find_latest_log()
                if latest and latest != path:
                    print(f"[info] Switching to newer log: {latest}")
                    f.close()
                    path = latest
                    f = open(path, "r", errors="ignore", encoding="utf-8", newline="")
                    f.seek(0, os.SEEK_END)
            time.sleep(0.5)
            continue

        for pat in JOIN_PATTERNS:
            if pat.search(line):
                name = extract_name(line)
                if name and is_self(name):
                    print(f"[skip] self joined: {name}")
                    break
                if name:
                    notify(f"Player joined: {name}")
                    print(f"[join] {name}")
                else:
                    # unknown name — still notify unless we KNOW it's self (we don't)
                    notify("A player joined your instance")
                    print("[join] <unknown>")
                break

def parse_args():
    # very small arg parser for: --self "NAME"
    self_name = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--self":
            if i + 1 >= len(args):
                print("Usage: vrc_join_notify.py [--self YOUR_DISPLAY_NAME]", file=sys.stderr)
                sys.exit(2)
            self_name = args[i+1]
            i += 2
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            print("Usage: vrc_join_notify.py [--self YOUR_DISPLAY_NAME]", file=sys.stderr)
            sys.exit(2)
    return self_name

def main():
    path = find_latest_log()
    if not path:
        print("VRChat log not found.", file=sys.stderr); sys.exit(2)
    override_cli = parse_args()
    self_name = detect_self_name(path, override_cli)
    try:
        tail_f(path, self_name)
    except KeyboardInterrupt:
        print("\n[info] Exiting."); sys.exit(0)

if __name__ == "__main__":
    main()

