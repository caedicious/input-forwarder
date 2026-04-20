"""
Input Forwarder - Sender (gaming PC side)

Captures mouse, keyboard, and Xbox controller inputs and forwards them via
UDP to a receiver on another machine on the LAN.

Config is stored at: %USERPROFILE%\input_forwarder_config.json
Delete it to re-run the first-time setup wizard.
"""

import socket
import ctypes
import ctypes.wintypes
import threading
import time
import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import mouse, keyboard

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

CONFIG_FILE = os.path.join(os.path.expanduser("~"), "input_forwarder_config.json")
DEFAULT_PORT = 7777

# ── VK Code Lookup ──────────────────────────────────────────────────────────

VK_NAMES = {
    0x08: "Backspace", 0x09: "Tab", 0x0D: "Enter", 0x10: "Shift", 0x11: "Ctrl",
    0x12: "Alt", 0x13: "Pause", 0x14: "CapsLock", 0x1B: "Escape", 0x20: "Space",
    0x21: "PageUp", 0x22: "PageDown", 0x23: "End", 0x24: "Home",
    0x25: "Left", 0x26: "Up", 0x27: "Right", 0x28: "Down",
    0x2D: "Insert", 0x2E: "Delete",
    0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4",
    0x35: "5", 0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9",
    0x41: "A", 0x42: "B", 0x43: "C", 0x44: "D", 0x45: "E",
    0x46: "F", 0x47: "G", 0x48: "H", 0x49: "I", 0x4A: "J",
    0x4B: "K", 0x4C: "L", 0x4D: "M", 0x4E: "N", 0x4F: "O",
    0x50: "P", 0x51: "Q", 0x52: "R", 0x53: "S", 0x54: "T",
    0x55: "U", 0x56: "V", 0x57: "W", 0x58: "X", 0x59: "Y", 0x5A: "Z",
    0x5B: "LWin", 0x5C: "RWin",
    0x60: "Numpad0", 0x61: "Numpad1", 0x62: "Numpad2", 0x63: "Numpad3",
    0x64: "Numpad4", 0x65: "Numpad5", 0x66: "Numpad6", 0x67: "Numpad7",
    0x68: "Numpad8", 0x69: "Numpad9",
    0x6A: "Numpad*", 0x6B: "Numpad+", 0x6D: "Numpad-", 0x6E: "Numpad.", 0x6F: "Numpad/",
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4", 0x74: "F5",
    0x75: "F6", 0x76: "F7", 0x77: "F8", 0x78: "F9", 0x79: "F10",
    0x7A: "F11", 0x7B: "F12",
    0x90: "NumLock", 0x91: "ScrollLock",
    0xA0: "LShift", 0xA1: "RShift", 0xA2: "LCtrl", 0xA3: "RCtrl",
    0xA4: "LAlt", 0xA5: "RAlt",
    0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".", 0xBF: "/", 0xC0: "`",
    0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'",
}

VK_FROM_NAME = {v: k for k, v in VK_NAMES.items()}

def pynput_key_to_vk(key):
    if hasattr(key, 'vk') and key.vk is not None:
        return key.vk
    if hasattr(key, 'value') and hasattr(key.value, 'vk'):
        return key.value.vk
    try:
        return key.value.vk
    except:
        pass
    special = {
        keyboard.Key.space: 0x20, keyboard.Key.enter: 0x0D, keyboard.Key.tab: 0x09,
        keyboard.Key.backspace: 0x08, keyboard.Key.esc: 0x1B, keyboard.Key.delete: 0x2E,
        keyboard.Key.insert: 0x2D, keyboard.Key.home: 0x24, keyboard.Key.end: 0x23,
        keyboard.Key.page_up: 0x21, keyboard.Key.page_down: 0x22,
        keyboard.Key.left: 0x25, keyboard.Key.up: 0x26, keyboard.Key.right: 0x27, keyboard.Key.down: 0x28,
        keyboard.Key.shift: 0x10, keyboard.Key.shift_l: 0xA0, keyboard.Key.shift_r: 0xA1,
        keyboard.Key.ctrl: 0x11, keyboard.Key.ctrl_l: 0xA2, keyboard.Key.ctrl_r: 0xA3,
        keyboard.Key.alt: 0x12, keyboard.Key.alt_l: 0xA4, keyboard.Key.alt_r: 0xA5,
        keyboard.Key.caps_lock: 0x14, keyboard.Key.num_lock: 0x90, keyboard.Key.scroll_lock: 0x91,
        keyboard.Key.pause: 0x13,
        keyboard.Key.f1: 0x70, keyboard.Key.f2: 0x71, keyboard.Key.f3: 0x72, keyboard.Key.f4: 0x73,
        keyboard.Key.f5: 0x74, keyboard.Key.f6: 0x75, keyboard.Key.f7: 0x76, keyboard.Key.f8: 0x77,
        keyboard.Key.f9: 0x78, keyboard.Key.f10: 0x79, keyboard.Key.f11: 0x7A, keyboard.Key.f12: 0x7B,
    }
    return special.get(key, None)

# ── Mouse/Controller Constants ──────────────────────────────────────────────

MOUSE_BUTTON_NAMES = {
    "left": "Left Click", "right": "Right Click", "middle": "Middle Click",
    "x1": "Mouse Back (X1)", "x2": "Mouse Forward (X2)",
}

MOUSE_OUTPUT_DATA = {
    "mouse_x1": {"is_mouse": True, "mouse_data": 0x0001, "vk": 0},
    "mouse_x2": {"is_mouse": True, "mouse_data": 0x0002, "vk": 0},
}

CONTROLLER_BUTTONS = {
    "dpad_up": ("D-Pad Up", 0x0001), "dpad_down": ("D-Pad Down", 0x0002),
    "dpad_left": ("D-Pad Left", 0x0004), "dpad_right": ("D-Pad Right", 0x0008),
    "start": ("Start", 0x0010), "back": ("Back", 0x0020),
    "left_thumb": ("Left Stick Press", 0x0040), "right_thumb": ("Right Stick Press", 0x0080),
    "left_shoulder": ("Left Bumper", 0x0100), "right_shoulder": ("Right Bumper", 0x0200),
    "a": ("A Button", 0x1000), "b": ("B Button", 0x2000),
    "x": ("X Button", 0x4000), "y": ("Y Button", 0x8000),
}

# ── XInput Setup ────────────────────────────────────────────────────────────

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [("wButtons", ctypes.c_ushort), ("bLeftTrigger", ctypes.c_ubyte),
                ("bRightTrigger", ctypes.c_ubyte), ("sThumbLX", ctypes.c_short),
                ("sThumbLY", ctypes.c_short), ("sThumbRX", ctypes.c_short),
                ("sThumbRY", ctypes.c_short)]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", ctypes.c_ulong), ("Gamepad", XINPUT_GAMEPAD)]

try:
    xinput = ctypes.windll.xinput1_4
except:
    try:
        xinput = ctypes.windll.xinput1_3
    except:
        try:
            xinput = ctypes.windll.xinput9_1_0
        except:
            xinput = None

XInputGetState = xinput.XInputGetState if xinput else None

# ── Screen detection (MWB compatibility) ────────────────────────────────────

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

screen_w = ctypes.windll.user32.GetSystemMetrics(0)
screen_h = ctypes.windll.user32.GetSystemMetrics(1)

def is_fullscreen_app():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    if not hwnd:
        return False
    rect = RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left <= 0 and rect.top <= 0 and
            rect.right >= screen_w and rect.bottom >= screen_h)

def cursor_on_local_screen():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    margin = 5
    return margin < pt.x < screen_w - margin and margin < pt.y < screen_h - margin

def should_send():
    if is_fullscreen_app():
        return True
    return cursor_on_local_screen()

# ── App ─────────────────────────────────────────────────────────────────────

class InputForwarderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Input Forwarder")
        self.root.geometry("720x560")
        self.root.resizable(True, True)

        self.armed = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mappings = []
        self.target_ip = ""
        self.target_port = DEFAULT_PORT
        self.mapping_counter = 0
        self.recording_trigger = False
        self.recording_output = False
        self.recorded_trigger = None
        self.recorded_output = None
        self.temp_trigger_name = ""
        self.temp_output_name = ""
        self.tray_icon = None

        self.load_config()
        if not self.target_ip:
            if not self.run_setup_wizard():
                self.root.destroy()
                return
            self.save_config()
        self.build_ui()
        self.start_listeners()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ── Setup wizard ────────────────────────────────────────────────────

    def run_setup_wizard(self):
        """Modal first-run dialog to collect target IP and port. Returns True on save."""
        self.root.withdraw()
        dlg = tk.Toplevel(self.root)
        dlg.title("Input Forwarder — First-Time Setup")
        dlg.geometry("420x240")
        dlg.resizable(False, False)
        dlg.grab_set()

        ttk.Label(dlg, text="First-time setup",
                  font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
        ttk.Label(dlg, text="Enter the LAN IP and UDP port of the receiver PC.",
                  wraplength=380, justify=tk.CENTER).pack(padx=15)

        form = ttk.Frame(dlg, padding=15)
        form.pack(fill=tk.X)

        ttk.Label(form, text="Target IP:", width=12).grid(row=0, column=0, sticky=tk.W, pady=4)
        ip_var = tk.StringVar()
        ttk.Entry(form, textvariable=ip_var, width=24).grid(row=0, column=1, pady=4)

        ttk.Label(form, text="Target Port:", width=12).grid(row=1, column=0, sticky=tk.W, pady=4)
        port_var = tk.StringVar(value=str(DEFAULT_PORT))
        ttk.Entry(form, textvariable=port_var, width=24).grid(row=1, column=1, pady=4)

        result = {"ok": False}

        def on_save():
            ip = ip_var.get().strip()
            if not ip:
                messagebox.showwarning("Missing", "Target IP is required.", parent=dlg)
                return
            try:
                port = int(port_var.get().strip())
            except ValueError:
                messagebox.showwarning("Invalid", "Port must be an integer.", parent=dlg)
                return
            if not (1 <= port <= 65535):
                messagebox.showwarning("Invalid", "Port must be between 1 and 65535.", parent=dlg)
                return
            self.target_ip = ip
            self.target_port = port
            result["ok"] = True
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        btn = ttk.Frame(dlg)
        btn.pack(pady=10)
        ttk.Button(btn, text="Save", command=on_save).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=6)

        self.root.wait_window(dlg)
        if result["ok"]:
            self.root.deiconify()
        return result["ok"]

    # ── UI ──────────────────────────────────────────────────────────────

    def build_ui(self):
        top_frame = ttk.Frame(self.root, padding=5)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Target IP:").pack(side=tk.LEFT, padx=(0, 5))
        self.ip_var = tk.StringVar(value=self.target_ip)
        ttk.Entry(top_frame, textvariable=self.ip_var, width=16).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(top_frame, text="Port:").pack(side=tk.LEFT, padx=(0, 5))
        self.port_var = tk.StringVar(value=str(self.target_port))
        ttk.Entry(top_frame, textvariable=self.port_var, width=6).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(top_frame, text="Apply", command=self.apply_connection).pack(side=tk.LEFT, padx=(0, 20))

        self.status_var = tk.StringVar(value="ARMED")
        self.status_label = ttk.Label(top_frame, textvariable=self.status_var,
                                       font=("Segoe UI", 11, "bold"), foreground="green")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        ttk.Label(top_frame, text="F9 to toggle |").pack(side=tk.RIGHT)

        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        list_frame = ttk.Frame(self.root, padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("trigger", "output", "mode", "filter", "enabled")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        self.tree.heading("trigger", text="Trigger Input")
        self.tree.heading("output", text="Output Key")
        self.tree.heading("mode", text="Mode")
        self.tree.heading("filter", text="Filter")
        self.tree.heading("enabled", text="Enabled")
        self.tree.column("trigger", width=180)
        self.tree.column("output", width=150)
        self.tree.column("mode", width=120)
        self.tree.column("filter", width=120)
        self.tree.column("enabled", width=60)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(self.root, padding=5)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Add Mapping", command=self.add_mapping_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Mapping", command=self.edit_mapping_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Mapping", command=self.delete_mapping).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Toggle Enabled", command=self.toggle_enabled).pack(side=tk.LEFT, padx=5)

        self.refresh_list()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, m in enumerate(self.mappings):
            self.tree.insert("", tk.END, iid=str(i), values=(
                m.get("trigger_name", "?"),
                m.get("output_name", "?"),
                m.get("mode", "?"),
                m.get("filter", "always"),
                "Yes" if m.get("enabled", True) else "No",
            ))

    # ── Mapping Dialog ──────────────────────────────────────────────────

    def add_mapping_dialog(self):
        self._mapping_dialog(None)

    def edit_mapping_dialog(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Edit", "Select a mapping to edit.")
            return
        self._mapping_dialog(int(sel[0]))

    def _mapping_dialog(self, edit_index):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Mapping" if edit_index is None else "Edit Mapping")
        dlg.geometry("450x500")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        existing = self.mappings[edit_index] if edit_index is not None else None

        # Trigger
        ttk.Label(dlg, text="Trigger Input:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 2))
        trigger_frame = ttk.Frame(dlg)
        trigger_frame.pack(fill=tk.X, padx=10)

        trigger_var = tk.StringVar(value=existing["trigger_name"] if existing else "Click to record...")
        ttk.Label(trigger_frame, textvariable=trigger_var, width=35, relief="sunken", padding=5).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.recorded_trigger = existing.get("trigger") if existing else None
        self.temp_trigger_name = existing.get("trigger_name", "") if existing else ""

        def record_trigger():
            trigger_var.set("Press any key, click, or controller button...")
            self.recording_trigger = True
            self.recorded_trigger = None
            self.temp_trigger_name = ""
            def wait():
                while self.recording_trigger:
                    time.sleep(0.01)
                dlg.after(0, lambda: trigger_var.set(self.temp_trigger_name or "None detected"))
            threading.Thread(target=wait, daemon=True).start()

        ttk.Button(trigger_frame, text="Record", command=record_trigger).pack(side=tk.RIGHT)

        # Output
        ttk.Label(dlg, text="Output Key:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(15, 2))
        output_frame = ttk.Frame(dlg)
        output_frame.pack(fill=tk.X, padx=10)

        output_var = tk.StringVar(value=existing["output_name"] if existing else "Click to record...")
        ttk.Label(output_frame, textvariable=output_var, width=35, relief="sunken", padding=5).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.recorded_output = existing.get("output") if existing else None
        self.temp_output_name = existing.get("output_name", "") if existing else ""

        def record_output():
            output_var.set("Press the key to send on PC2...")
            self.recording_output = True
            self.recorded_output = None
            self.temp_output_name = ""
            def wait():
                while self.recording_output:
                    time.sleep(0.01)
                dlg.after(0, lambda: output_var.set(self.temp_output_name or "None detected"))
            threading.Thread(target=wait, daemon=True).start()

        ttk.Button(output_frame, text="Record", command=record_output).pack(side=tk.RIGHT)

        ttk.Label(dlg, text="— or select mouse button output —", font=("Segoe UI", 8)).pack(pady=(2, 0))
        mouse_out_frame = ttk.Frame(dlg)
        mouse_out_frame.pack(fill=tk.X, padx=10)

        def set_mouse_output(name, key):
            self.recording_output = False
            data = MOUSE_OUTPUT_DATA[key]
            self.recorded_output = {"type": key, **data}
            self.temp_output_name = name
            output_var.set(name)

        ttk.Button(mouse_out_frame, text="Mouse Back (X1)",
                   command=lambda: set_mouse_output("Mouse Back (X1)", "mouse_x1")).pack(side=tk.LEFT, padx=2)
        ttk.Button(mouse_out_frame, text="Mouse Fwd (X2)",
                   command=lambda: set_mouse_output("Mouse Forward (X2)", "mouse_x2")).pack(side=tk.LEFT, padx=2)

        # Mode
        ttk.Label(dlg, text="Mode:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(15, 2))
        mode_var = tk.StringVar(value=existing["mode"] if existing else "single")
        mode_frame = ttk.Frame(dlg)
        mode_frame.pack(fill=tk.X, padx=10)
        for val, text in [("single", "Single Press"), ("hold", "Hold"),
                          ("repeat", "Repeat (spam)"),
                          ("repeat_paired", "Repeat Paired (always ends off)"),
                          ("toggle_repeat", "Toggle + Repeat"),
                          ("press_both", "Press on Down + Press on Release")]:
            ttk.Radiobutton(mode_frame, text=text, variable=mode_var, value=val).pack(anchor=tk.W)

        interval_frame = ttk.Frame(dlg)
        interval_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        ttk.Label(interval_frame, text="Repeat interval (seconds):").pack(side=tk.LEFT)
        interval_var = tk.StringVar(value=str(existing.get("interval", 0.05)) if existing else "0.05")
        ttk.Entry(interval_frame, textvariable=interval_var, width=8).pack(side=tk.LEFT, padx=5)

        # Filter
        ttk.Label(dlg, text="Filter:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 2))
        filter_var = tk.StringVar(value=existing.get("filter", "always") if existing else "always")
        filter_frame = ttk.Frame(dlg)
        filter_frame.pack(fill=tk.X, padx=10)
        ttk.Radiobutton(filter_frame, text="Always send", variable=filter_var, value="always").pack(anchor=tk.W)
        ttk.Radiobutton(filter_frame, text="Only when cursor on local screen / fullscreen app",
                        variable=filter_var, value="local_screen").pack(anchor=tk.W)

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(fill=tk.X, padx=10, pady=15)

        def save():
            if not self.recorded_trigger or not self.recorded_output:
                messagebox.showwarning("Missing", "Please record both trigger and output.")
                return
            try:
                interval = float(interval_var.get())
            except:
                interval = 0.05

            self.mapping_counter += 1
            mapping = {
                "id": existing["id"] if existing else f"mapping_{self.mapping_counter}",
                "trigger": self.recorded_trigger,
                "trigger_name": self.temp_trigger_name,
                "output": self.recorded_output,
                "output_name": self.temp_output_name,
                "mode": mode_var.get(),
                "interval": interval,
                "filter": filter_var.get(),
                "enabled": existing.get("enabled", True) if existing else True,
            }

            if edit_index is not None:
                self.mappings[edit_index] = mapping
            else:
                self.mappings.append(mapping)

            self.save_config()
            self.refresh_list()
            dlg.destroy()

        ttk.Button(btn_frame, text="Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side=tk.LEFT, padx=5)

    def delete_mapping(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select a mapping to delete.")
            return
        idx = int(sel[0])
        name = self.mappings[idx].get("trigger_name", "?")
        if messagebox.askyesno("Delete", f"Delete mapping: {name}?"):
            self.mappings.pop(idx)
            self.save_config()
            self.refresh_list()

    def toggle_enabled(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self.mappings[idx]["enabled"] = not self.mappings[idx].get("enabled", True)
        self.save_config()
        self.refresh_list()

    def apply_connection(self):
        self.target_ip = self.ip_var.get()
        try:
            self.target_port = int(self.port_var.get())
        except:
            self.target_port = DEFAULT_PORT
        self.save_config()

    # ── Config ──────────────────────────────────────────────────────────

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                self.target_ip = data.get("target_ip", "")
                self.target_port = data.get("target_port", DEFAULT_PORT)
                self.mappings = data.get("mappings", [])
                self.mapping_counter = data.get("mapping_counter", 0)
            except:
                pass

    def save_config(self):
        data = {
            "target_ip": self.target_ip,
            "target_port": self.target_port,
            "mappings": self.mappings,
            "mapping_counter": self.mapping_counter,
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # ── Input listeners ─────────────────────────────────────────────────

    def start_listeners(self):
        self.kb_listener = keyboard.Listener(on_press=self.on_kb_press, on_release=self.on_kb_release)
        self.kb_listener.start()

        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()

        threading.Thread(target=self.poll_mouse_x1, daemon=True).start()

        if XInputGetState:
            threading.Thread(target=self.poll_controller, daemon=True).start()

    def on_kb_press(self, key):
        if key == keyboard.Key.f9:
            self.armed = not self.armed
            self.root.after(0, lambda: self.status_var.set("ARMED" if self.armed else "DISARMED"))
            self.root.after(0, lambda: self.status_label.configure(
                foreground="green" if self.armed else "red"))
            if HAS_TRAY and self.tray_icon:
                self.tray_icon.icon = self.create_tray_icon()
            return

        if self.recording_trigger:
            vk = pynput_key_to_vk(key)
            if vk:
                name = VK_NAMES.get(vk, f"Key 0x{vk:02X}")
                self.recorded_trigger = {"type": "keyboard", "vk": vk}
                self.temp_trigger_name = f"Keyboard: {name}"
                self.recording_trigger = False
            return

        if self.recording_output:
            vk = pynput_key_to_vk(key)
            if vk:
                name = VK_NAMES.get(vk, f"Key 0x{vk:02X}")
                self.recorded_output = {"type": "keyboard", "vk": vk, "is_mouse": False, "mouse_data": 0}
                self.temp_output_name = name
                self.recording_output = False
            return

        if not self.armed:
            return
        vk = pynput_key_to_vk(key)
        if vk:
            self.check_and_send({"type": "keyboard", "vk": vk}, "press")

    def on_kb_release(self, key):
        if not self.armed:
            return
        vk = pynput_key_to_vk(key)
        if vk:
            self.check_and_send({"type": "keyboard", "vk": vk}, "release")

    def on_mouse_click(self, x, y, button, pressed):
        btn_name = button.name

        if self.recording_trigger and pressed and btn_name != "x1":
            self.recorded_trigger = {"type": f"mouse_{btn_name}"}
            self.temp_trigger_name = f"Mouse: {MOUSE_BUTTON_NAMES.get(btn_name, btn_name)}"
            self.recording_trigger = False
            return

        if not self.armed or btn_name == "x1":
            return

        self.check_and_send({"type": f"mouse_{btn_name}"}, "press" if pressed else "release")

    def poll_mouse_x1(self):
        VK_XBUTTON1 = 0x05
        was_down = False
        while True:
            state = ctypes.windll.user32.GetAsyncKeyState(VK_XBUTTON1)
            is_down = bool(state & 0x8000)

            if self.recording_trigger and is_down and not was_down:
                self.recorded_trigger = {"type": "mouse_x1"}
                self.temp_trigger_name = "Mouse: Back (X1)"
                self.recording_trigger = False
                was_down = is_down
                time.sleep(0.001)
                continue

            if self.armed:
                if is_down and not was_down:
                    self.check_and_send({"type": "mouse_x1"}, "press")
                elif not is_down and was_down:
                    self.check_and_send({"type": "mouse_x1"}, "release")
            was_down = is_down
            time.sleep(0.001)

    def poll_controller(self):
        prev_buttons = 0
        prev_rt = False
        prev_lt = False
        state = XINPUT_STATE()
        TRIGGER_THRESHOLD = 50

        while True:
            result = XInputGetState(0, ctypes.byref(state))
            if result == 0:
                buttons = state.Gamepad.wButtons
                rt_down = state.Gamepad.bRightTrigger > TRIGGER_THRESHOLD
                lt_down = state.Gamepad.bLeftTrigger > TRIGGER_THRESHOLD

                for btn_key, (btn_name, btn_mask) in CONTROLLER_BUTTONS.items():
                    now = bool(buttons & btn_mask)
                    was = bool(prev_buttons & btn_mask)
                    if now and not was:
                        if self.recording_trigger:
                            self.recorded_trigger = {"type": f"controller_{btn_key}"}
                            self.temp_trigger_name = f"Controller: {btn_name}"
                            self.recording_trigger = False
                        elif self.armed:
                            self.check_and_send({"type": f"controller_{btn_key}"}, "press")
                    elif not now and was and self.armed:
                        self.check_and_send({"type": f"controller_{btn_key}"}, "release")

                if rt_down and not prev_rt:
                    if self.recording_trigger:
                        self.recorded_trigger = {"type": "controller_right_trigger"}
                        self.temp_trigger_name = "Controller: Right Trigger"
                        self.recording_trigger = False
                    elif self.armed:
                        self.check_and_send({"type": "controller_right_trigger"}, "press")
                elif not rt_down and prev_rt and self.armed:
                    self.check_and_send({"type": "controller_right_trigger"}, "release")

                if lt_down and not prev_lt:
                    if self.recording_trigger:
                        self.recorded_trigger = {"type": "controller_left_trigger"}
                        self.temp_trigger_name = "Controller: Left Trigger"
                        self.recording_trigger = False
                    elif self.armed:
                        self.check_and_send({"type": "controller_left_trigger"}, "press")
                elif not lt_down and prev_lt and self.armed:
                    self.check_and_send({"type": "controller_left_trigger"}, "release")

                prev_buttons = buttons
                prev_rt = rt_down
                prev_lt = lt_down

            time.sleep(0.001)

    # ── Send ────────────────────────────────────────────────────────────

    def check_and_send(self, trigger, action):
        for m in self.mappings:
            if not m.get("enabled", True):
                continue
            if m["trigger"]["type"] != trigger["type"]:
                continue
            if trigger["type"] == "keyboard" and m["trigger"].get("vk") != trigger.get("vk"):
                continue
            if m.get("filter") == "local_screen" and not should_send():
                continue

            output = m["output"]
            msg = {
                "id": m["id"],
                "action": action,
                "mode": m["mode"],
                "vk": output.get("vk", 0),
                "is_mouse": output.get("is_mouse", False),
                "mouse_data": output.get("mouse_data", 0),
                "interval": m.get("interval", 0.05),
            }
            try:
                self.sock.sendto(json.dumps(msg).encode(), (self.target_ip, self.target_port))
            except:
                pass

    # ── Tray ────────────────────────────────────────────────────────────

    def create_tray_icon(self):
        img = Image.new('RGB', (64, 64), color=(40, 40, 40))
        draw = ImageDraw.Draw(img)
        draw.ellipse([12, 12, 52, 52], fill='lime' if self.armed else 'red')
        return img

    def on_tray_open(self, icon, item):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def on_tray_toggle(self, icon, item):
        self.armed = not self.armed
        self.root.after(0, lambda: self.status_var.set("ARMED" if self.armed else "DISARMED"))
        self.root.after(0, lambda: self.status_label.configure(
            foreground="green" if self.armed else "red"))
        icon.icon = self.create_tray_icon()

    def on_tray_quit(self, icon, item):
        icon.stop()
        self.save_config()
        self.root.after(0, self.root.destroy)

    def minimize_to_tray(self):
        if not HAS_TRAY:
            self.root.iconify()
            return
        self.root.withdraw()
        menu = pystray.Menu(
            pystray.MenuItem("Open", self.on_tray_open, default=True),
            pystray.MenuItem("Toggle Armed", self.on_tray_toggle),
            pystray.MenuItem("Quit", self.on_tray_quit),
        )
        self.tray_icon = pystray.Icon("InputForwarder", self.create_tray_icon(), "Input Forwarder", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_close(self):
        self.save_config()
        self.minimize_to_tray()


if __name__ == "__main__":
    root = tk.Tk()
    app = InputForwarderApp(root)
    root.mainloop()
