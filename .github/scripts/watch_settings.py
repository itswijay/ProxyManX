"""Log Windows "environment changed" broadcasts, used by CI only.

Usage: python watch_settings.py LOGFILE

Each broadcast is logged with the HTTP_PROXY value saved in the registry at
that moment. That is what Explorer would read, and so what a new terminal
would get.
"""

import ctypes
import sys
import winreg
from ctypes import wintypes

WM_SETTINGCHANGE = 0x1A
LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HANDLE, wintypes.HANDLE, wintypes.LPVOID,
]


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT), ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HANDLE), ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR),
    ]


def log(line):
    with open(sys.argv[1], "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")


def saved_http_proxy():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            return winreg.QueryValueEx(key, "HTTP_PROXY")[0]
    except FileNotFoundError:
        return ""


@WNDPROC
def on_message(hwnd, message, wparam, lparam):
    if message == WM_SETTINGCHANGE and lparam and ctypes.wstring_at(lparam) == "Environment":
        log(f"Environment HTTP_PROXY={saved_http_proxy()}")
    return user32.DefWindowProcW(hwnd, message, wparam, lparam)


window_class = WNDCLASS(lpfnWndProc=on_message, lpszClassName="ProxyManXWatch")
if not user32.RegisterClassW(ctypes.byref(window_class)):
    raise ctypes.WinError(ctypes.get_last_error())
# A hidden top-level window: message-only windows do not receive broadcasts
if not user32.CreateWindowExW(0, "ProxyManXWatch", "", 0, 0, 0, 0, 0, None, None, None, None):
    raise ctypes.WinError(ctypes.get_last_error())

log("WATCHING")
message = wintypes.MSG()
while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
    user32.DispatchMessageW(ctypes.byref(message))
