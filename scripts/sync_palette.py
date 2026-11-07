#!/usr/bin/env python3
"""
Caelestia Windows - Material You (M3) Dynamic Color & Wallpaper Engine.
Extracts dominant vibrant hue from the current Windows wallpaper (or sets a new one)
and generates full Material 3 tonal palettes (Dark & Light) matching caelestia-shell.
"""

from __future__ import annotations

import argparse
import colorsys
import ctypes
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import winreg
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None


PROJECT_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_DIR / "state.json"
WALLPAPER_DIR = Path.home() / "Pictures" / "Wallpapers"


# --- Perceptual OKLab / OKLCH Color Math for genuine Material 3 Tonal Ramps ---

def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055


def rgb_to_oklch(r: int, g: int, b: int) -> tuple[float, float, float]:
    lr, lg, lb = srgb_to_linear(r / 255.0), srgb_to_linear(g / 255.0), srgb_to_linear(b / 255.0)
    l_ = (0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb) ** (1.0 / 3.0)
    m_ = (0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb) ** (1.0 / 3.0)
    s_ = (0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb) ** (1.0 / 3.0)

    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b_val = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_

    C = math.hypot(a, b_val)
    H = math.degrees(math.atan2(b_val, a)) % 360.0
    return L, C, H


def oklch_in_gamut(L: float, C: float, H: float) -> tuple[bool, tuple[float, float, float]]:
    rad = math.radians(H)
    a = C * math.cos(rad)
    b_val = C * math.sin(rad)

    l_ = L + 0.3963377774 * a + 0.2158037573 * b_val
    m_ = L - 0.1055613458 * a - 0.0638541728 * b_val
    s_ = L - 0.0894841775 * a - 1.2914855480 * b_val

    l3, m3, s3 = l_ ** 3, m_ ** 3, s_ ** 3
    lr = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
    lg = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
    lb = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3

    eps = -0.0005
    hi = 1.0005
    ok = (eps <= lr <= hi) and (eps <= lg <= hi) and (eps <= lb <= hi)
    return ok, (lr, lg, lb)


def tone_to_hex(tone: float, max_chroma: float, hue: float) -> str:
    """Convert M3 tone (0..100), target OKLCH chroma, and hue (0..360) into sRGB hex."""
    if tone <= 0.5:
        return "#000000"
    if tone >= 99.5:
        return "#ffffff"

    # Map M3 tone (0..100) smoothly to OKLab L (0..1)
    L = max(0.0, min(1.0, (tone / 100.0) ** 0.92))
    # Binary search highest in-gamut chroma up to max_chroma
    low, high = 0.0, max_chroma
    best_rgb = (L, L, L)
    ok_full, rgb_full = oklch_in_gamut(L, max_chroma, hue)
    if ok_full:
        best_rgb = rgb_full
    else:
        for _ in range(14):
            mid = (low + high) * 0.5
            ok, rgb = oklch_in_gamut(L, mid, hue)
            if ok:
                low = mid
                best_rgb = rgb
            else:
                high = mid

    r = int(round(linear_to_srgb(best_rgb[0]) * 255))
    g = int(round(linear_to_srgb(best_rgb[1]) * 255))
    b = int(round(linear_to_srgb(best_rgb[2]) * 255))
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_seed_color(image_path: Path) -> tuple[int, int, int]:
    """Score dominant vibrant colors from wallpaper (Material You style)."""
    default_seed = (168, 98, 123)  # Caelestia signature rose-mauve (#a8627b)
    if Image is None or not image_path.exists():
        return default_seed

    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB").resize((80, 80))
            buckets: dict[int, list[float]] = {}
            pixels = img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()
            for r, g, b in pixels:
                L, C, H = rgb_to_oklch(r, g, b)
                if L < 0.12 or L > 0.94:
                    continue
                bucket = int(H // 10) % 36
                # Prefer vibrant mid-tone colors
                vibrancy_weight = 1.0 + (C * 8.0) ** 1.5
                lightness_weight = 1.0 - abs(L - 0.58) * 0.8
                score = vibrancy_weight * max(0.2, lightness_weight)
                if bucket not in buckets:
                    buckets[bucket] = [0.0, 0.0, 0.0, 0.0]
                buckets[bucket][0] += score
                buckets[bucket][1] += r * score
                buckets[bucket][2] += g * score
                buckets[bucket][3] += b * score

            if not buckets:
                return default_seed

            best = max(buckets.values(), key=lambda v: v[0])
            total = best[0]
            return (int(best[1] / total), int(best[2] / total), int(best[3] / total))
    except Exception:
        return default_seed


def build_m3_palette(seed_rgb: tuple[int, int, int], mode: str = "dark") -> dict[str, str]:
    _, seed_c, hue = rgb_to_oklch(*seed_rgb)
    # Ensure pleasant chroma even on muted wallpapers
    p_c = max(0.11, min(0.18, seed_c * 1.15 if seed_c > 0.03 else 0.13))
    s_c = p_c * 0.38
    t_c = p_c * 0.75
    t_hue = (hue + 52.0) % 360.0
    n_c = 0.016
    nv_c = 0.034

    if mode == "dark":
        return {
            "mode": "dark",
            "seed": f"#{seed_rgb[0]:02x}{seed_rgb[1]:02x}{seed_rgb[2]:02x}",
            "m3background": tone_to_hex(8, n_c, hue),
            "m3onBackground": tone_to_hex(91, n_c, hue),
            "m3surface": tone_to_hex(9, n_c, hue),
            "m3surfaceDim": tone_to_hex(7, n_c, hue),
            "m3surfaceBright": tone_to_hex(24, n_c, hue),
            "m3surfaceContainerLowest": tone_to_hex(5, n_c, hue),
            "m3surfaceContainerLow": tone_to_hex(12, n_c, hue),
            "m3surfaceContainer": tone_to_hex(15, n_c, hue),
            "m3surfaceContainerHigh": tone_to_hex(20, n_c, hue),
            "m3surfaceContainerHighest": tone_to_hex(25, n_c, hue),
            "m3onSurface": tone_to_hex(92, n_c, hue),
            "m3surfaceVariant": tone_to_hex(30, nv_c, hue),
            "m3onSurfaceVariant": tone_to_hex(80, nv_c, hue),
            "m3outline": tone_to_hex(60, nv_c, hue),
            "m3outlineVariant": tone_to_hex(30, nv_c, hue),
            "m3primary": tone_to_hex(80, p_c, hue),
            "m3onPrimary": tone_to_hex(20, p_c, hue),
            "m3primaryContainer": tone_to_hex(30, p_c, hue),
            "m3onPrimaryContainer": tone_to_hex(90, p_c, hue),
            "m3secondary": tone_to_hex(80, s_c, hue),
            "m3onSecondary": tone_to_hex(20, s_c, hue),
            "m3secondaryContainer": tone_to_hex(30, s_c, hue),
            "m3onSecondaryContainer": tone_to_hex(90, s_c, hue),
            "m3tertiary": tone_to_hex(80, t_c, t_hue),
            "m3onTertiary": tone_to_hex(20, t_c, t_hue),
            "m3tertiaryContainer": tone_to_hex(32, t_c, t_hue),
            "m3onTertiaryContainer": tone_to_hex(92, t_c, t_hue),
            "m3error": "#ffb4ab",
            "m3onError": "#690005",
            "m3errorContainer": "#93000a",
            "m3success": "#b5ccba",
            "m3successContainer": "#374b3e",
        }
    else:
        return {
            "mode": "light",
            "seed": f"#{seed_rgb[0]:02x}{seed_rgb[1]:02x}{seed_rgb[2]:02x}",
            "m3background": tone_to_hex(98, n_c, hue),
            "m3onBackground": tone_to_hex(12, n_c, hue),
            "m3surface": tone_to_hex(97, n_c, hue),
            "m3surfaceDim": tone_to_hex(88, n_c, hue),
            "m3surfaceBright": tone_to_hex(99, n_c, hue),
            "m3surfaceContainerLowest": "#ffffff",
            "m3surfaceContainerLow": tone_to_hex(95, n_c, hue),
            "m3surfaceContainer": tone_to_hex(92, n_c, hue),
            "m3surfaceContainerHigh": tone_to_hex(88, n_c, hue),
            "m3surfaceContainerHighest": tone_to_hex(84, n_c, hue),
            "m3onSurface": tone_to_hex(12, n_c, hue),
            "m3surfaceVariant": tone_to_hex(88, nv_c, hue),
            "m3onSurfaceVariant": tone_to_hex(32, nv_c, hue),
            "m3outline": tone_to_hex(50, nv_c, hue),
            "m3outlineVariant": tone_to_hex(80, nv_c, hue),
            "m3primary": tone_to_hex(42, p_c, hue),
            "m3onPrimary": "#ffffff",
            "m3primaryContainer": tone_to_hex(89, p_c, hue),
            "m3onPrimaryContainer": tone_to_hex(14, p_c, hue),
            "m3secondary": tone_to_hex(42, s_c, hue),
            "m3onSecondary": "#ffffff",
            "m3secondaryContainer": tone_to_hex(89, s_c, hue),
            "m3onSecondaryContainer": tone_to_hex(15, s_c, hue),
            "m3tertiary": tone_to_hex(42, t_c, t_hue),
            "m3onTertiary": "#ffffff",
            "m3tertiaryContainer": tone_to_hex(89, t_c, t_hue),
            "m3onTertiaryContainer": tone_to_hex(15, t_c, t_hue),
            "m3error": "#ba1a1a",
            "m3onError": "#ffffff",
            "m3errorContainer": "#ffdad6",
            "m3success": "#386a48",
            "m3successContainer": "#bbf0c6",
        }


def get_current_windows_wallpaper() -> Path:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
            val, _ = winreg.QueryValueEx(key, "WallPaper")
            if val and Path(val).exists():
                return Path(val)
    except Exception:
        pass
    transcoded = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Themes" / "TranscodedWallpaper"
    if transcoded.exists():
        return transcoded
    return PROJECT_DIR / "zebar-pack" / "assets" / "wallpaper.webp"


def set_windows_wallpaper(image_path: Path) -> None:
    resolved = str(image_path.resolve())
    SPI_SETDESKWALLPAPER = 0x0014
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDWININICHANGE = 0x02
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, resolved, SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
    )


def list_candidate_wallpapers() -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    candidates: list[Path] = []
    for folder in [
        WALLPAPER_DIR,
        Path.home() / "Pictures",
        Path(r"C:\Windows\Web\Wallpaper\Windows"),
        Path(r"C:\Windows\Web\Wallpaper\Theme1"),
        Path(r"C:\Windows\Web\Wallpaper\ThemeA"),
        Path(r"C:\Windows\Web\Wallpaper\ThemeB"),
        Path(r"C:\Windows\Web\4K\Wallpaper\Windows"),
    ]:
        if folder.exists():
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in exts:
                    candidates.append(f)
    return candidates


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"mode": "dark", "wallpaper": ""}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def camel_to_kebab(name: str) -> str:
    s = re.sub(r"^m3", "m3-", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s).lower()


def write_palette_outputs(palette: dict[str, str], wallpaper: Path) -> None:
    lines = [":root {"]
    for key, val in palette.items():
        if key in ("mode", "seed"):
            continue
        lines.append(f"  --{camel_to_kebab(key)}: {val};")
    lines.append(f"  --m3-seed: {palette['seed']};")
    lines.append("}")
    css_text = "\n".join(lines) + "\n"

    candidates = list_candidate_wallpapers()[:10]
    wall_entries = []
    targets = [
        PROJECT_DIR / "zebar-pack",
        Path.home() / ".glzr" / "zebar" / "caelestia-shell",
    ]
    for idx, cand in enumerate(candidates):
        thumb_rel = f"./assets/wall_thumbs/thumb_{idx}.jpg"
        wall_entries.append({
            "name": cand.stem,
            "path": str(cand.resolve()),
            "thumb": thumb_rel,
        })
        if Image is not None and cand.exists():
            for target in targets:
                if target.exists():
                    thumb_dir = target / "assets" / "wall_thumbs"
                    thumb_dir.mkdir(parents=True, exist_ok=True)
                    thumb_file = thumb_dir / f"thumb_{idx}.jpg"
                    if not thumb_file.exists():
                        try:
                            with Image.open(cand) as im:
                                im.convert("RGB").resize((320, 180)).save(thumb_file, quality=82)
                        except Exception:
                            pass

    payload = {
        "wallpaperName": wallpaper.name,
        "wallpaperPath": str(wallpaper.resolve()) if wallpaper.exists() else "",
        "palette": palette,
        "wallpapers": wall_entries,
    }
    js_text = f"window.__CAELESTIA_THEME__ = {json.dumps(payload, indent=2)};\n"

    for target in targets:
        if target.exists():
            (target / "palette.css").write_text(css_text, encoding="utf-8")
            (target / "palette.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
            (target / "palette.js").write_text(js_text, encoding="utf-8")
            # Copy preview thumbnail so WebView can display current wallpaper card
            if Image is not None and wallpaper.exists():
                try:
                    with Image.open(wallpaper) as im:
                        im.convert("RGB").resize((480, 270)).save(target / "assets" / "current_wall.jpg", quality=86)
                except Exception:
                    pass

    # Update GlazeWM active border color if config exists
    glaze_cfg = Path.home() / ".glzr" / "glazewm" / "config.yaml"
    if glaze_cfg.exists():
        content = glaze_cfg.read_text(encoding="utf-8")
        updated = re.sub(
            r"(focused_window:\s*\n\s*border:\s*\n\s*enabled:\s*true\s*\n\s*color:\s*')#[0-9a-fA-F]{6}(')",
            rf"\g<1>{palette['m3primary']}\2",
            content,
        )
        updated = re.sub(
            r"(other_windows:\s*\n\s*border:\s*\n\s*enabled:\s*true\s*\n\s*color:\s*')#[0-9a-fA-F]{6}(')",
            rf"\g<1>{palette['m3outlineVariant']}\2",
            updated,
        )
        if updated != content:
            glaze_cfg.write_text(updated, encoding="utf-8")
            portable_cli = PROJECT_DIR / "bin" / "glazewm-extract" / "PFiles64" / "glzr.io" / "GlazeWM" / "cli" / "glazewm.exe"
            glaze_bin = str(portable_cli) if portable_cli.exists() else shutil.which("glazewm")
            if glaze_bin:
                subprocess.run(
                    [glaze_bin, "command", "wm-reload-config"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )


def main() -> None:
    parser = argparse.ArgumentParser(description="Caelestia Material You Dynamic Theme Sync")
    parser.add_argument("--wallpaper", "-f", type=str, help="Set specific wallpaper file and sync colors")
    parser.add_argument("--random", "-r", action="store_true", help="Pick a random wallpaper and sync colors")
    parser.add_argument("--mode", "-m", choices=["dark", "light"], help="Set dark or light scheme")
    parser.add_argument("--toggle-mode", "-t", action="store_true", help="Toggle between dark and light mode")
    args = parser.parse_args()

    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    # Seed ~/Pictures/Wallpapers with Caelestia default wallpaper & current wallpaper if empty
    caelestia_wp = Path(r"C:\Users\uypc1\.gemini\antigravity\scratch\caelestia-shell\assets\wallpaper.webp")
    if caelestia_wp.exists() and not any(WALLPAPER_DIR.iterdir()):
        shutil.copy2(caelestia_wp, WALLPAPER_DIR / "caelestia_default.webp")
        curr = get_current_windows_wallpaper()
        if curr.exists() and curr.suffix:
            shutil.copy2(curr, WALLPAPER_DIR / curr.name)

    state = load_state()
    mode = state.get("mode", "dark")
    if args.mode:
        mode = args.mode
    elif args.toggle_mode:
        mode = "light" if mode == "dark" else "dark"

    if args.wallpaper:
        wp = Path(args.wallpaper).expanduser()
        if wp.exists():
            set_windows_wallpaper(wp)
    elif args.random:
        pool = list_candidate_wallpapers()
        current_str = state.get("wallpaper", "")
        filtered = [p for p in pool if str(p.resolve()) != current_str] or pool
        if filtered:
            wp = random.choice(filtered)
            set_windows_wallpaper(wp)
        else:
            wp = get_current_windows_wallpaper()
    else:
        wp = get_current_windows_wallpaper()

    seed = extract_seed_color(wp)
    palette = build_m3_palette(seed, mode=mode)
    state["mode"] = mode
    state["wallpaper"] = str(wp.resolve()) if wp.exists() else ""
    save_state(state)
    write_palette_outputs(palette, wp)
    print(f"[OK] Synced Caelestia M3 ({mode}) from {wp.name} -> primary {palette['m3primary']}")


if __name__ == "__main__":
    main()
