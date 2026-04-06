
# note requires jp2a and ncspot

import argparse
import json
import os
import socket
import subprocess
import sys
import time

from pathlib import Path
from shutil import which
from typing import Final

NCSPOT_SOCKET_NAME: Final[str] = "ncspot.sock"


def detect_socket_path(explicit: Path | None) -> Path | None:

    if explicit:
        return Path(explicit).expanduser()

    ncspot_bin = which("ncspot")
    if not ncspot_bin:
        raise RuntimeError("ncspot not found in path")

    try:
        proc = subprocess.run(
            [ncspot_bin, "info"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    cache_dir: Path | None = None
    runtime_dir: Path | None = None

    for line in proc.stdout.splitlines():
        if "USER_CACHE_PATH" in line:
            _, sep, value = line.partition(" ")
            if sep:
                cache_dir = Path(value.strip())

        if "USER_RUNTIME_PATH" in line:
            _, sep, value = line.partition(" ")
            if sep:
                runtime_dir = Path(value.strip())

    if runtime_dir and (runtime_dir / NCSPOT_SOCKET_NAME).exists():
        return runtime_dir / NCSPOT_SOCKET_NAME

    if cache_dir and (cache_dir / NCSPOT_SOCKET_NAME).exists():
        return cache_dir / NCSPOT_SOCKET_NAME

    return None
    

def stream_now_playing(socket_path: Path, timeout: float):

    while True:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
    
            sock.settimeout(timeout)
            sock.connect(str(socket_path))
            sock.sendall(b"\n")
            sock.settimeout(None)

            with sock.makefile("r", encoding="utf-8") as stream:
                for line in stream:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

        except (OSError, TimeoutError) as exc:
            print(f"[ncspot-ascii] socket error: {exc}", file=sys.stderr)
            time.sleep(2)
        finally:
            sock.close()


def render_with_jp2a(url: str) -> None:

    jp2a_bin = which("jp2a")
    if not jp2a_bin:
        raise RuntimeError("jp2a not found in path")

    cmd = [jp2a_bin, "--color", "--term-zoom", "--term-center", "--background=dark", "--clear", "--fill"]
    cmd.append(url)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("jp2a failed: {}".format(exc))
    

def wait_for_socket(explicit: Path | None = None, poll_interval: float = 1.0) -> Path:

    socket_path: Path | None = None

    while not socket_path or not socket_path.exists():
        print("waiting for socket...")
        time.sleep(poll_interval)
        socket_path = detect_socket_path(explicit=explicit)

    return socket_path


def build_arg_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Connect to the ncspot IPC socket, optain the current album cover URL, and render it with jp2a."
        )
    )

    parser.add_argument(
        "--socket",
        help="Path to the ncspot IPC socket (defaults to the selected path).",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="Socket timeout (seconds) for contacting ncspot.",
    )

    parser.add_argument(
        "--reconnect-timeout",
        type=int,
        default=2,
        help="Reconnect timeout in seconds.",
    )

    return parser


def main() -> None:

    parser = build_arg_parser()
    args = parser.parse_args()

    socket_path = wait_for_socket(args.socket)

    last_cover_url: str | None = None
    for payload in stream_now_playing(socket_path, args.timeout):
        playable = payload.get("playable", {})

        if not playable:
            time.sleep(args.timeout)
            continue

        cover_url = playable.get("cover_url")


        if not cover_url or cover_url == last_cover_url:
            continue

        last_cover_url = cover_url
        render_with_jp2a(cover_url)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        sys.exit("error: {}".format(exc))








