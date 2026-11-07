import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32

def cb(hwnd, extra):
    if not user32.IsWindowVisible(hwnd):
        return True
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    if w <= 0 or h <= 0:
        return True
    
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, title, 512)
    cls = ctypes.create_unicode_buffer(512)
    user32.GetClassNameW(hwnd, cls, 512)
    exstyle = user32.GetWindowLongW(hwnd, -20)
    
    # Check if around our dashboard (w=780, h=335, left ~406) or bar (w=56)
    if (w == 780 or w == 56 or rect.left == 406 or rect.left == 0):
        print(f"HWND: {hwnd}, PID: {pid.value}, Class: {cls.value}, Title: '{title.value}', Rect: ({rect.left}, {rect.top}, {rect.right}, {rect.bottom}), ExStyle: {hex(exstyle)}")
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
user32.EnumWindows(WNDENUMPROC(cb), 0)
