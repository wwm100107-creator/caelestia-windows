#!/usr/bin/env python3
"""
Caelestia Windows - Top Edge Mouse Trigger & Auto-retract Daemon.
1. Trigger open ONLY when cursor hits top edge (y <= 2) WITHIN the dashboard width.
2. Monitor cursor position: if outside dashboard bounds for >= 1.0s, trigger close.
3. Single-instance PID management to prevent duplicate processes on Zebar reload.
"""

from __future__ import annotations

import ctypes
import os
import sys
import time
from pathlib import Path

# Force unbuffered stdout
if sys.stdout:
    sys.stdout.reconfigure(line_buffering=True)

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

user32 = ctypes.windll.user32
pt = POINT()

PROJECT_DIR = Path(__file__).resolve().parent.parent
FLAG_FILE = PROJECT_DIR / "dashboard.open"
PID_FILE = PROJECT_DIR / "mouse_edge.pid"

# Single-instance enforcement: kill previous instance if still running
my_pid = os.getpid()
if PID_FILE.exists():
    try:
        old_pid = int(PID_FILE.read_text().strip())
        if old_pid != my_pid:
            # Terminate old instance
            os.system(f"taskkill /F /PID {old_pid} >nul 2>&1")
            time.sleep(0.1)
    except Exception:
        pass

try:
    PID_FILE.write_text(str(my_pid))
except Exception:
    pass

# Clean up stale flag on start
if FLAG_FILE.exists():
    try:
        FLAG_FILE.unlink()
    except Exception:
        pass


def start_media_thumbnail_listener() -> None:
    """Background thread polling Windows GSMTC for active video/audio thumbnail."""
    try:
        import asyncio
        import threading
        from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
        from winsdk.windows.storage.streams import DataReader
    except Exception:
        return

    dest_paths = [
        PROJECT_DIR / "zebar-pack" / "assets" / "media_thumb.jpg",
        Path.home() / ".glzr" / "zebar" / "caelestia-shell" / "assets" / "media_thumb.jpg",
    ]

    async def poll_once(state: dict[str, str]) -> None:
        try:
            mgr = await GlobalSystemMediaTransportControlsSessionManager.request_async()
            s = mgr.get_current_session()
            if not s:
                return
            prop = await s.try_get_media_properties_async()
            title = prop.title or ""
            if title != state.get("title"):
                state["title"] = title
                thumb_ref = prop.thumbnail
                if thumb_ref:
                    stream = await thumb_ref.open_read_async()
                    size = stream.size
                    if size > 0:
                        reader = DataReader(stream)
                        await reader.load_async(size)
                        data = bytearray(size)
                        reader.read_bytes(data)
                        for dest in dest_paths:
                            try:
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                dest.write_bytes(data)
                            except Exception:
                                pass
        except Exception:
            pass

    def run_loop() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        state = {"title": ""}
        while True:
            try:
                loop.run_until_complete(poll_once(state))
            except Exception:
                pass
            time.sleep(1.0)

    th = threading.Thread(target=run_loop, daemon=True)
    th.start()


def clear_zebar_dwm_border() -> None:
    """Remove Windows 11 DWM rectangular border from transparent Zebar container window."""
    try:
        dwmapi = ctypes.windll.dwmapi
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        none_color = ctypes.c_uint32(0xFFFFFFFE)  # DWMWA_COLOR_NONE
        no_round = ctypes.c_uint32(1)             # DWMWCP_DONOTROUND

        def _enum_cb(hwnd: int, _lparam: int) -> bool:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if "Zebar" in buf.value:
                dwmapi.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(none_color), 4)
                dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(no_round), 4)
            return True

        user32.EnumWindows(WNDENUMPROC(_enum_cb), 0)
    except Exception:
        pass


def get_dashboard_bounds() -> tuple[int, int, int]:
    """Calculate the screen bounds of the top dashboard."""
    screen_w = user32.GetSystemMetrics(0)
    # Primary monitor center (matches Zebar preset offsetX: 0px)
    center_x = screen_w // 2
    dash_w = 736                        # Exact width of drawer body
    left_x = center_x - (dash_w // 2)
    right_x = center_x + (dash_w // 2)
    card_bottom_y = 365                 # Visible height of the drawer card
    return left_x, right_x, card_bottom_y


def main() -> None:
    start_media_thumbnail_listener()
    clear_zebar_dwm_border()
    left_x, right_x, bottom_y = get_dashboard_bounds()
    outside_since: float | None = None
    is_open = False
    last_trigger = 0.0
    last_bounds_check = time.time()

    try:
        while True:
            time.sleep(0.015)  # ~65 checks/sec: 0% CPU, microsecond responsiveness for 0.1s timer

            now = time.time()
            # Recalculate bounds periodically in case of resolution change
            if now - last_bounds_check > 2.0:
                left_x, right_x, bottom_y = get_dashboard_bounds()
                clear_zebar_dwm_border()
                last_bounds_check = now

            if not user32.GetCursorPos(ctypes.byref(pt)):
                continue

            # Check external flag file (e.g. opened/closed via Bar buttons or Esc)
            flag_exists = FLAG_FILE.exists()
            if flag_exists and not is_open:
                is_open = True
                outside_since = None
            elif not flag_exists and is_open and outside_since is None:
                # Dashboard was closed externally
                is_open = False

            if not is_open:
                outside_since = None
                # REQUIREMENT 1: ONLY trigger when cursor hits top edge (y <= 2)
                # STRICTLY within the dashboard width (left_x <= pt.x <= right_x)
                if pt.y <= 2 and (left_x <= pt.x <= right_x):
                    if now - last_trigger > 0.8:
                        last_trigger = now
                        is_open = True
                        try:
                            FLAG_FILE.touch()
                        except Exception:
                            pass
                        print("TRIGGER_OPEN", flush=True)
                        clear_zebar_dwm_border()
                        time.sleep(0.15)
            else:
                # Dashboard is currently open
                # Check if cursor is inside the visible dashboard card
                # Generous 15px margin to avoid accidental retraction near borders
                is_inside = (left_x - 15 <= pt.x <= right_x + 15) and (0 <= pt.y <= bottom_y + 15)

                if is_inside:
                    outside_since = None
                else:
                    # REQUIREMENT 2: Reliable OS-level 0.1s outside timer
                    if outside_since is None:
                        outside_since = now
                    elif now - outside_since >= 0.1:
                        is_open = False
                        outside_since = None
                        try:
                            if FLAG_FILE.exists():
                                FLAG_FILE.unlink()
                        except Exception:
                            pass
                        print("TRIGGER_CLOSE", flush=True)
                        time.sleep(0.15)
    finally:
        # Clean up PID file on exit
        if PID_FILE.exists():
            try:
                PID_FILE.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    main()
