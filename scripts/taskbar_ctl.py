#!/usr/bin/env python3
"""
Safe, official Win32 AppBar controller to toggle Windows 11 Taskbar auto-hide
without killing explorer.exe or patching system files.
"""

import argparse
import ctypes
from ctypes import wintypes

ABM_GETSTATE = 0x00000004
ABM_SETSTATE = 0x0000000A
ABS_AUTOHIDE = 0x00000001
ABS_ALWAYSONTOP = 0x00000002


class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]


def set_taskbar_autohide(enable: bool) -> None:
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32

    hwnd = user32.FindWindowW("Shell_TrayWnd", None)
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)
    abd.hWnd = hwnd
    abd.lParam = (ABS_AUTOHIDE | ABS_ALWAYSONTOP) if enable else ABS_ALWAYSONTOP
    shell32.SHAppBarMessage(ABM_SETSTATE, ctypes.byref(abd))


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--autohide", action="store_true", help="Enable taskbar auto-hide")
    group.add_argument("--restore", action="store_true", help="Restore persistent Windows taskbar")
    args = parser.parse_args()

    set_taskbar_autohide(args.autohide)
    print(f"[OK] Taskbar auto-hide = {args.autohide}")


if __name__ == "__main__":
    main()
