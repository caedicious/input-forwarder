"""
Input Forwarder - Receiver (stream PC side)

Listens for UDP messages from the sender and simulates the described key or
mouse events via Win32 SendInput. Must be run as administrator for SendInput
to work across all foreground windows.

Config is stored at: %USERPROFILE%\input_forwarder_receiver.json
Delete it to re-run the first-time setup wizard.
"""

import socket
import time
import threading
import ctypes
import json
import os

CONFIG_FILE = os.path.join(os.path.expanduser("~"), "input_forwarder_receiver.json")
HOST = "0.0.0.0"
DEFAULT_PORT = 7777


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def run_setup_wizard():
    """Modal first-run dialog to collect listen port. Returns the port or None."""
    import tkinter as tk
    from tkinter import ttk, messagebox

    root = tk.Tk()
    root.title("Input Forwarder Receiver — First-Time Setup")
    root.geometry("420x220")
    root.resizable(False, False)

    ttk.Label(root, text="First-time setup",
              font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
    ttk.Label(root,
              text="Choose the UDP port to listen on. Must match the port "
                   "configured on the sender PC.",
              wraplength=380, justify=tk.CENTER).pack(padx=15)

    form = ttk.Frame(root, padding=15)
    form.pack(fill=tk.X)

    ttk.Label(form, text="Listen Port:", width=12).grid(row=0, column=0, sticky=tk.W, pady=4)
    port_var = tk.StringVar(value=str(DEFAULT_PORT))
    ttk.Entry(form, textvariable=port_var, width=24).grid(row=0, column=1, pady=4)

    result = {"port": None}

    def on_save():
        try:
            port = int(port_var.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid", "Port must be an integer.", parent=root)
            return
        if not (1 <= port <= 65535):
            messagebox.showwarning("Invalid", "Port must be between 1 and 65535.", parent=root)
            return
        result["port"] = port
        root.destroy()

    def on_cancel():
        root.destroy()

    btn = ttk.Frame(root)
    btn.pack(pady=10)
    ttk.Button(btn, text="Save", command=on_save).pack(side=tk.LEFT, padx=6)
    ttk.Button(btn, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=6)

    root.mainloop()
    return result["port"]


config = load_config()
PORT = config.get("port")
if not PORT:
    PORT = run_setup_wizard()
    if not PORT:
        raise SystemExit("Setup cancelled — no port configured.")
    save_config({"port": PORT})

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

SendInput = ctypes.windll.user32.SendInput
MapVirtualKeyW = ctypes.windll.user32.MapVirtualKeyW
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                 ("wScan", ctypes.c_ushort),
                 ("dwFlags", ctypes.c_ulong),
                 ("time", ctypes.c_ulong),
                 ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                 ("wParamL", ctypes.c_short),
                 ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                 ("dy", ctypes.c_long),
                 ("mouseData", ctypes.c_ulong),
                 ("dwFlags", ctypes.c_ulong),
                 ("time", ctypes.c_ulong),
                 ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                 ("ii", Input_I)]

KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100

EXTENDED_VKS = {0xA3, 0xA1, 0xA5, 0x5B, 0x5C, 0x21, 0x22, 0x23, 0x24,
                0x2D, 0x2E, 0x25, 0x26, 0x27, 0x28, 0x6F, 0x90}

def send_key_down(vk):
    scan = MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_SCANCODE
    if vk in EXTENDED_VKS:
        flags |= KEYEVENTF_EXTENDEDKEY
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(vk, scan, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def send_key_up(vk):
    scan = MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
    if vk in EXTENDED_VKS:
        flags |= KEYEVENTF_EXTENDEDKEY
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(vk, scan, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def send_mouse_down(button_data):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, button_data, MOUSEEVENTF_XDOWN, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def send_mouse_up(button_data):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, button_data, MOUSEEVENTF_XUP, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def tap(vk, is_mouse, mouse_data):
    if is_mouse:
        send_mouse_down(mouse_data)
        time.sleep(0.05)
        send_mouse_up(mouse_data)
    else:
        send_key_down(vk)
        time.sleep(0.05)
        send_key_up(vk)

# State tracking per mapping
mapping_state = {}   # desired state: True = should be active
vnyan_state = {}     # actual state: True = currently active
mapping_configs = {}
active_repeats = {}
state_lock = threading.Lock()

def state_worker():
    """Single worker that ensures output state matches desired state."""
    while True:
        with state_lock:
            for mid in list(mapping_state.keys()):
                desired = mapping_state.get(mid, False)
                actual = vnyan_state.get(mid, False)
                cfg = mapping_configs.get(mid)
                if cfg is None:
                    continue

                mode = cfg["mode"]
                vk = cfg["vk"]
                is_mouse = cfg["is_mouse"]
                mouse_data = cfg["mouse_data"]
                interval = cfg["interval"]

                if mode == "press_both":
                    if desired and not actual:
                        tap(vk, is_mouse, mouse_data)
                        vnyan_state[mid] = True
                    elif not desired and actual:
                        tap(vk, is_mouse, mouse_data)
                        vnyan_state[mid] = False

                elif mode == "repeat_paired":
                    if desired and not actual:
                        tap(vk, is_mouse, mouse_data)
                        vnyan_state[mid] = True
                    elif desired and actual:
                        tap(vk, is_mouse, mouse_data)
                        vnyan_state[mid] = False
                    elif not desired and actual:
                        tap(vk, is_mouse, mouse_data)
                        vnyan_state[mid] = False

                elif mode == "toggle_repeat":
                    if desired and not actual:
                        tap(vk, is_mouse, mouse_data)
                        vnyan_state[mid] = True
                    elif not desired and actual:
                        tap(vk, is_mouse, mouse_data)
                        vnyan_state[mid] = False
                    elif desired and actual:
                        tap(vk, is_mouse, mouse_data)
                        time.sleep(interval)
                        tap(vk, is_mouse, mouse_data)

        time.sleep(0.05)

def handle_message(msg):
    try:
        data = json.loads(msg)
    except:
        return

    mid = data.get("id", "unknown")
    action = data.get("action")
    mode = data.get("mode")
    vk = data.get("vk", 0)
    is_mouse = data.get("is_mouse", False)
    mouse_data = data.get("mouse_data", 0)
    interval = data.get("interval", 0.05)

    mapping_configs[mid] = {
        "mode": mode, "vk": vk, "is_mouse": is_mouse,
        "mouse_data": mouse_data, "interval": interval
    }

    if mode in ("press_both", "toggle_repeat", "repeat_paired"):
        with state_lock:
            mapping_state[mid] = (action == "press")

    elif mode == "single":
        if action == "press":
            tap(vk, is_mouse, mouse_data)

    elif mode == "hold":
        if action == "press":
            if is_mouse:
                send_mouse_down(mouse_data)
            else:
                send_key_down(vk)
        elif action == "release":
            if is_mouse:
                send_mouse_up(mouse_data)
            else:
                send_key_up(vk)

    elif mode == "repeat":
        if action == "press":
            active_repeats[mid] = True
            def do_repeat():
                while active_repeats.get(mid, False):
                    tap(vk, is_mouse, mouse_data)
                    time.sleep(interval)
            threading.Thread(target=do_repeat, daemon=True).start()
        elif action == "release":
            active_repeats[mid] = False

def udp_listener():
    while True:
        data, addr = sock.recvfrom(4096)
        handle_message(data.decode())

threading.Thread(target=state_worker, daemon=True).start()
threading.Thread(target=udp_listener, daemon=True).start()

while True:
    time.sleep(1)
