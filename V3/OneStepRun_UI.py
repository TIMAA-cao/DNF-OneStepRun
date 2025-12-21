import customtkinter as ctk
import ctypes
import os
import time
import threading
import json
import win32gui
import win32api
import sys
from PIL import Image, ImageDraw 

# =============================================================================
# 0. 辅助功能
# =============================================================================

def get_real_path(filename):
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, filename)

def play_mp3_native(filename):
    file_path = get_real_path(filename)
    if not os.path.exists(file_path): return
    def _worker():
        alias = f"mp3_{int(time.time()*1000)}" 
        try:
            mci = ctypes.windll.winmm.mciSendStringW
            mci(f'open "{file_path}" type mpegvideo alias {alias}', None, 0, 0)
            mci(f'play {alias} wait', None, 0, 0)
            mci(f'close {alias}', None, 0, 0)
        except: pass
    threading.Thread(target=_worker, daemon=True).start()

def create_dynamic_icon(filename, color_hex, shape="rect"):
    size = (64, 64)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if shape == "circle":
        draw.ellipse((4, 4, 60, 60), fill=color_hex, outline="white", width=3)
        draw.polygon([(24, 16), (24, 48), (48, 32)], fill="white")
    else:
        draw.rounded_rectangle((4, 4, 60, 60), radius=10, fill=color_hex, outline="white", width=3)
        draw.rectangle((22, 18, 28, 46), fill="white")
        draw.rectangle((36, 18, 42, 46), fill="white")
    icon_path = get_real_path(filename)
    image.save(icon_path, format="ICO")
    return icon_path

# =============================================================================
# 1. 配置与键码
# =============================================================================
CONFIG_FILE = "run_config.json"

VK_MAP = {
    'LBUTTON': 0x01, 'RBUTTON': 0x02, 'MBUTTON': 0x04,
    'BACKSPACE': 0x08, 'TAB': 0x09, 'ENTER': 0x0D,
    'SFT': 0x10, 'CTL': 0x11, 'ALT': 0x12, 'PAUSE': 0x13, 'CAPS': 0x14, 
    'ESC': 0x1B, 'SPACE': 0x20, 
    'LWIN': 0x5B, 'RWIN': 0x5C, 'APPS': 0x5D,
    'LSHIFT': 0xA0, 'RSHIFT': 0xA1, 'LCONTROL': 0xA2, 'RCONTROL': 0xA3, 'LALT': 0xA4, 'RALT': 0xA5,
    'PRINTSCREEN': 0x2C, 'SCROLLLOCK': 0x91, 'NUMLOCK': 0x90,
    'PAGEUP': 0x21, 'PAGEDOWN': 0x22, 'END': 0x23, 'HOME': 0x24, 
    'LEFT': 0x25, 'UP': 0x26, 'RIGHT': 0x27, 'DOWN': 0x28,
    'INSERT': 0x2D, 'DELETE': 0x2E,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46, 'G': 0x47,
    'H': 0x48, 'I': 0x49, 'J': 0x4A, 'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E,
    'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54, 'U': 0x55,
    'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A,
    'NUMPAD_0': 0x60, 'NUMPAD_1': 0x61, 'NUMPAD_2': 0x62, 'NUMPAD_3': 0x63,
    'NUMPAD_4': 0x64, 'NUMPAD_5': 0x65, 'NUMPAD_6': 0x66, 'NUMPAD_7': 0x67,
    'NUMPAD_8': 0x68, 'NUMPAD_9': 0x69, 
    'NUMPAD_MULTIPLY': 0x6A, 'NUMPAD_PLUS': 0x6B, 'NUMPAD_MINUS': 0x6D, 
    'NUMPAD_DOT': 0x6E, 'NUMPAD_DIVIDE': 0x6F, 'NUMPAD_ENTER': 0x0D,
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74, 'F6': 0x75,
    'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
    'SEMICOLON': 0xBA, 'EQUAL': 0xBB, 'COMMA': 0xBC, 'MINUS': 0xBD, 'PERIOD': 0xBE,
    'SLASH': 0xBF, 'GRAVE': 0xC0, 'LBRACKET': 0xDB, 'BACKSLASH': 0xDC, 'RBRACKET': 0xDD, 'QUOTE': 0xDE
}

# 硬件扫描码表
SCANCODE_MAP = {
    'ESC': 0x01, '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05, '5': 0x06, '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A, '0': 0x0B, 'MINUS': 0x0C, 'EQUAL': 0x0D, 'BACKSPACE': 0x0E, 'TAB': 0x0F,
    'Q': 0x10, 'W': 0x11, 'E': 0x12, 'R': 0x13, 'T': 0x14, 'Y': 0x15, 'U': 0x16, 'I': 0x17, 'O': 0x18, 'P': 0x19, 'LBRACKET': 0x1A, 'RBRACKET': 0x1B, 'ENTER': 0x1C, 'CTL': 0x1D,
    'A': 0x1E, 'S': 0x1F, 'D': 0x20, 'F': 0x21, 'G': 0x22, 'H': 0x23, 'J': 0x24, 'K': 0x25, 'L': 0x26, 'SEMICOLON': 0x27, 'QUOTE': 0x28, 'GRAVE': 0x29, 'LSHIFT': 0x2A, 'BACKSLASH': 0x2B,
    'Z': 0x2C, 'X': 0x2D, 'C': 0x2E, 'V': 0x2F, 'B': 0x30, 'N': 0x31, 'M': 0x32, 'COMMA': 0x33, 'PERIOD': 0x34, 'SLASH': 0x35, 'RSHIFT': 0x36, 'NUMPAD_MULTIPLY': 0x37, 'ALT': 0x38, 'SPACE': 0x39,
    'CAPS': 0x3A, 'F1': 0x3B, 'F2': 0x3C, 'F3': 0x3D, 'F4': 0x3E, 'F5': 0x3F, 'F6': 0x40, 'F7': 0x41, 'F8': 0x42, 'F9': 0x43, 'F10': 0x44, 'NUMLOCK': 0x45, 'SCROLLLOCK': 0x46,
    'NUMPAD_7': 0x47, 'NUMPAD_8': 0x48, 'NUMPAD_9': 0x49, 'NUMPAD_MINUS': 0x4A, 'NUMPAD_4': 0x4B, 'NUMPAD_5': 0x4C, 'NUMPAD_6': 0x4D, 'NUMPAD_PLUS': 0x4E, 'NUMPAD_1': 0x4F, 'NUMPAD_2': 0x50, 'NUMPAD_3': 0x51, 'NUMPAD_0': 0x52, 'NUMPAD_DOT': 0x53,
    'F11': 0x57, 'F12': 0x58,
    
    # 扩展键
    'UP': 0xC8, 'LEFT': 0xCB, 'RIGHT': 0xCD, 'DOWN': 0xD0,
    'INSERT': 0xD2, 'DELETE': 0xD3, 'HOME': 0xC7, 'END': 0xCF, 'PAGEUP': 0xC9, 'PAGEDOWN': 0xD1,
    'NUMPAD_ENTER': 0x9C, 'RCONTROL': 0x9D, 'NUMPAD_DIVIDE': 0xB5, 'PRINTSCREEN': 0xB7, 'RALT': 0xB8,
}

class ConfigManager:
    DEFAULT_CONFIG = {
        "trigger_up": "UP", "trigger_down": "DOWN", "trigger_left": "LEFT", "trigger_right": "RIGHT",
        "output_up": "UP", "output_down": "DOWN", "output_left": "LEFT", "output_right": "RIGHT",
        "switch_key": "F12"           
    }
    @staticmethod
    def load():
        path = get_real_path(CONFIG_FILE)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in ConfigManager.DEFAULT_CONFIG.items():
                        if k not in data: data[k] = v
                    return data
            except: pass
        return ConfigManager.DEFAULT_CONFIG.copy()
    @staticmethod
    def save(config_data):
        try:
            path = get_real_path(CONFIG_FILE)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except: pass

# =============================================================================
# 2. 原生 API 结构体 (适配 64位/32位 Python)
# =============================================================================
LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(DWORD) 
WORD = ctypes.c_ushort

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (('dx', LONG),
                ('dy', LONG),
                ('mouseData', DWORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (('wVk', WORD),
                ('wScan', WORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (('uMsg', DWORD),
                ('wParamL', WORD),
                ('wParamH', WORD))

class _INPUTunion(ctypes.Union):
    _fields_ = (('mi', MOUSEINPUT),
                ('ki', KEYBDINPUT),
                ('hi', HARDWAREINPUT))

class INPUT(ctypes.Structure):
    _fields_ = (('type', DWORD),
                ('union', _INPUTunion))

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_SCANCODE    = 0x0008

class NativeKeyboard:
    def __init__(self):
        self.ok = True 
        self.user32 = ctypes.windll.user32
        self.game_keys = {} 

    def update_game_keys(self, config):
        
        for key_type in ['output_up', 'output_down', 'output_left', 'output_right']:
            key_name = config[key_type]
            scancode = SCANCODE_MAP.get(key_name)
            is_extended = key_name in ['UP', 'DOWN', 'LEFT', 'RIGHT', 'INSERT', 'DELETE', 'HOME', 'END', 'PAGEUP', 'PAGEDOWN', 'R_ALT', 'R_CTL']
            
            if scancode is None:
                vk = VK_MAP.get(key_name, 0)
                if vk:
                    scancode = self.user32.MapVirtualKeyW(vk, 0)
                else:
                    scancode = 0
            
            internal_name = key_type.replace('output', 'GAME').upper()
            self.game_keys[internal_name] = (scancode, is_extended)

    def _send_input(self, scancode, is_extended, is_up):
        flags = KEYEVENTF_SCANCODE
        if is_extended: flags |= KEYEVENTF_EXTENDEDKEY
        if is_up: flags |= KEYEVENTF_KEYUP
        
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = 0
        inp.union.ki.wScan = scancode
        inp.union.ki.dwFlags = flags
        inp.union.ki.time = 0
        inp.union.ki.dwExtraInfo = None 
        
        self.user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

    def press(self, key_alias):
        if key_alias in self.game_keys:
            sc, ext = self.game_keys[key_alias]
            if sc: self._send_input(sc, ext, False)

    def release(self, key_alias):
        if key_alias in self.game_keys:
            sc, ext = self.game_keys[key_alias]
            if sc: self._send_input(sc, ext, True)

# =============================================================================
# 3. 核心逻辑
# =============================================================================
def is_physically_down(vk_code):
    if vk_code is None or vk_code == 0: return False
    return (ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000) != 0

class DirectMapper:
    def __init__(self, kb, output_alias, trigger_vk_code):
        self.kb = kb
        self.output_key = output_alias 
        self.trigger_vk = trigger_vk_code
        self.was_down = False

    def update_trigger(self, trigger_vk_code):
        self.trigger_vk = trigger_vk_code

    def force_stop(self):
        if self.was_down:
            self.kb.release(self.output_key)
            self.was_down = False

    def process(self):
        is_down = is_physically_down(self.trigger_vk)
        if is_down and not self.was_down:
            self.kb.press(self.output_key)
        elif not is_down and self.was_down:
            self.kb.release(self.output_key)
        self.was_down = is_down

class SafeRunner:
    def __init__(self, kb, output_alias, trigger_vk_code, other_runner=None):
        self.kb = kb
        self.output_key = output_alias
        self.trigger_vk = trigger_vk_code 
        self.state = "IDLE" 
        self.other_runner = other_runner
        self.press_time = 0.0      
        self.was_phys_down = False 

    def update_trigger(self, trigger_vk_code):
        self.trigger_vk = trigger_vk_code

    def force_stop(self):
        if self.state != "IDLE":
            self.kb.release(self.output_key)
            self.state = "IDLE"

    def process(self):
        phys_down = is_physically_down(self.trigger_vk)
        if phys_down and not self.was_phys_down:
            self.press_time = time.time()
        self.was_phys_down = phys_down
        
        if phys_down:
            if self.other_runner and self.other_runner.was_phys_down:
                if self.press_time < self.other_runner.press_time:
                    self.force_stop()
                    return 

        if phys_down:
            if self.state == "IDLE":
                if self.other_runner: self.other_runner.force_stop()
                self.state = "RUNNING"

                self.kb.press(self.output_key) 
                time.sleep(0.02) 
                self.kb.release(self.output_key)
                time.sleep(0.04) 
                self.kb.press(self.output_key)
                
            elif self.state == "RUNNING":
                pass
        else:
            if self.state == "RUNNING":
                self.kb.release(self.output_key)
                self.state = "IDLE"

# =============================================================================
# 4. 后台逻辑线程
# =============================================================================
class LogicThread(threading.Thread):
    def __init__(self, kb, app_ref):
        super().__init__()
        self.kb = kb
        self.app_ref = app_ref 
        self.daemon = True
        self.running = True
        self.enabled = False 
        self.runner_left = SafeRunner(kb, 'GAME_LEFT', 0)
        self.runner_right = SafeRunner(kb, 'GAME_RIGHT', 0)
        self.runner_left.other_runner = self.runner_right
        self.runner_right.other_runner = self.runner_left
        self.mapper_up = DirectMapper(kb, 'GAME_UP', 0)
        self.mapper_down = DirectMapper(kb, 'GAME_DOWN', 0)
        self.current_switch_vk = 0
        self.last_switch_state = False
        self.game_active = False 

    def update_settings(self, config):
        self.kb.update_game_keys(config)
        self.runner_left.update_trigger(VK_MAP.get(config['trigger_left'], 0))
        self.runner_right.update_trigger(VK_MAP.get(config['trigger_right'], 0))
        self.mapper_up.update_trigger(VK_MAP.get(config['trigger_up'], 0))
        self.mapper_down.update_trigger(VK_MAP.get(config['trigger_down'], 0))
        self.current_switch_vk = VK_MAP.get(config['switch_key'], 0)

    def run(self):
        while self.running:
            if self.current_switch_vk:
                curr_sw = is_physically_down(self.current_switch_vk)
                if curr_sw and not self.last_switch_state:
                    self.app_ref.toggle_from_logic(not self.enabled)
                self.last_switch_state = curr_sw

            self.game_active = self._is_game_active() 

            if self.enabled and self.kb.ok and self.game_active:
                self.runner_left.process()
                self.runner_right.process()
                self.mapper_up.process()
                self.mapper_down.process()
            else:
                if self.runner_left.state != "IDLE": self.runner_left.force_stop()
                if self.runner_right.state != "IDLE": self.runner_right.force_stop()
                self.mapper_up.force_stop()
                self.mapper_down.force_stop()
            
            time.sleep(0.001)

    def _is_game_active(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd: return False 
            title = win32gui.GetWindowText(hwnd)
            if "地下城" in title or "DNF" in title or "WeGame" in title: return True
            return False
        except: return False

# =============================================================================
# 5. UI 部分
# =============================================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class KeySelectorWindow(ctk.CTkToplevel):
    def __init__(self, parent, title_text, current_key, callback):
        super().__init__(parent)
        self.callback = callback
        self.title(title_text) 
        self.geometry("1450x550")
        self.minsize(1000, 400)
        self.attributes("-topmost", True)
        self.grab_set() 
        try:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            self.geometry(f"+{(sw-1450)//2}+{(sh-600)//2}")
        except: pass
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a")
        self.scroll_container.pack(fill="both", expand=True)
        self.content_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.content_frame.pack(anchor="center", pady=40, padx=20)
        ctk.CTkLabel(self.content_frame, text=f"{title_text}", font=("微软雅黑", 24, "bold"), text_color="#00FF00").pack(pady=(0, 20))
        self._setup_keyboard_layout(current_key)
        self.lift()
        self.focus_force()

    def _setup_keyboard_layout(self, current_key):
        # 左侧主键盘区域
        main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_frame.pack(side="left", anchor="n", padx=(0, 20))

        # Row 0
        row0 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row0.pack(fill="x", pady=(0, 15))
        self.create_key(row0, "ESC", current_key, w=60) 
        self.spacer(row0, 45) 
        for k in ['F1', 'F2', 'F3', 'F4']: self.create_key(row0, k, current_key, w=55)
        self.spacer(row0, 35)
        for k in ['F5', 'F6', 'F7', 'F8']: self.create_key(row0, k, current_key, w=55)
        self.spacer(row0, 35)
        for k in ['F9', 'F10', 'F11', 'F12']: self.create_key(row0, k, current_key, w=55)

        # Row 1
        row1 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        keys_r1 = [('GRAVE', '~'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('0', '0'), ('MINUS', '-'), ('EQUAL', '='), ('BACKSPACE', 'Backspace')]
        for code, txt in keys_r1:
            w = 110 if code == 'BACKSPACE' else 55
            self.create_key(row1, code, current_key, w=w, text=txt)

        # Row 2
        row2 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        self.create_key(row2, "TAB", current_key, w=85, text="Tab")
        keys_r2 = ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', ('LBRACKET', '['), ('RBRACKET', ']'), ('BACKSLASH', '\\')]
        for item in keys_r2:
            code, txt = (item[0], item[1]) if isinstance(item, tuple) else (item, item)
            w = 80 if code == 'BACKSLASH' else 55
            self.create_key(row2, code, current_key, w=w, text=txt)

        # Row 3
        row3 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row3.pack(fill="x", pady=2)
        self.create_key(row3, "CAPS", current_key, w=100, text="Caps")
        keys_r3 = ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ('SEMICOLON', ';'), ('QUOTE', "'")]
        for item in keys_r3:
            code, txt = (item[0], item[1]) if isinstance(item, tuple) else (item, item)
            self.create_key(row3, code, current_key, w=55, text=txt)
        self.create_key(row3, "ENTER", current_key, w=120, text="Enter")

        # Row 4
        row4 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row4.pack(fill="x", pady=2)
        self.create_key(row4, "SFT", current_key, w=130, text="L_Shift")
        keys_r4 = ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ('COMMA', ','), ('PERIOD', '.'), ('SLASH', '/')]
        for item in keys_r4:
            code, txt = (item[0], item[1]) if isinstance(item, tuple) else (item, item)
            self.create_key(row4, code, current_key, w=55, text=txt)
        self.create_key(row4, "R_SFT", current_key, w=145, text="R_Shift")

        # Row 5
        row5 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row5.pack(fill="x", pady=2)
        bottom_keys = [("CTL", "Ctrl", 70), ("LWIN", "Win", 70), ("ALT", "Alt", 70), ("SPACE", "Space", 370), ("R_ALT", "Alt", 70), ("RWIN", "Win", 70), ("APPS", "Menu", 70), ("R_CTL", "Ctrl", 70)]
        for code, txt, w in bottom_keys:
            self.create_key(row5, code, current_key, w=w, text=txt)

        # 中间区域：功能键 + 方向键
        mid_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        mid_frame.pack(side="left", anchor="n", padx=10)
        
        sys_row = ctk.CTkFrame(mid_frame, fg_color="transparent")
        sys_row.pack(fill="x", pady=(0, 15))
        for k, t in [("PRINTSCREEN", "PrtSc"), ("SCROLLLOCK", "ScrLk"), ("PAUSE", "Pause")]: self.create_key(sys_row, k, current_key, w=55, text=t, text_size=9)
        
        nav_grid = ctk.CTkFrame(mid_frame, fg_color="transparent")
        nav_grid.pack(fill="x")
        nav_keys = [[("INSERT", "Ins"), ("HOME", "Home"), ("PAGEUP", "PgUp")], [("DELETE", "Del"), ("END", "End"), ("PAGEDOWN", "PgDn")]]
        for row_data in nav_keys:
            row_f = ctk.CTkFrame(nav_grid, fg_color="transparent")
            row_f.pack(pady=2)
            for code, txt in row_data: self.create_key(row_f, code, current_key, w=55, text=txt, text_size=10)

        ctk.CTkLabel(mid_frame, text="", height=45).pack() 
        
        arrow_frame = ctk.CTkFrame(mid_frame, fg_color="transparent")
        arrow_frame.pack(side="bottom", pady=2)
        up_f = ctk.CTkFrame(arrow_frame, fg_color="transparent")
        up_f.pack()
        self.create_key(up_f, "UP", current_key, w=55, text="↑")
        down_f = ctk.CTkFrame(arrow_frame, fg_color="transparent")
        down_f.pack()
        self.create_key(down_f, "LEFT", current_key, w=55, text="←")
        self.create_key(down_f, "DOWN", current_key, w=55, text="↓")
        self.create_key(down_f, "RIGHT", current_key, w=55, text="→")

        # 右侧：小键盘
        numpad_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        numpad_frame.pack(side="left", anchor="n", padx=(20, 0))
        ctk.CTkLabel(numpad_frame, text="", height=40).pack() 
        
        np_grid = ctk.CTkFrame(numpad_frame, fg_color="transparent")
        np_grid.pack()
        
        def np_btn(r, c, code, txt=None, h=40, w=55, rs=1, cs=1):
            if not txt: txt = code.split("_")[-1]
            is_selected = (code == current_key)
            b = ctk.CTkButton(np_grid, text=txt, width=w, height=h, 
                            fg_color="#00CC66" if is_selected else "#2B2B2B",
                            hover_color="#00994D" if is_selected else "#3A3A3A",
                            text_color="white", border_width=2 if is_selected else 1,
                            border_color="#00CC66" if is_selected else "#444444",
                            font=("Arial", 11, "bold"), command=lambda k=code: self.on_key_click(k))
            b.grid(row=r, column=c, rowspan=rs, columnspan=cs, padx=2, pady=2)

        np_btn(0, 0, "NUMLOCK", "Num"); np_btn(0, 1, "NUMPAD_DIVIDE", "/"); np_btn(0, 2, "NUMPAD_MULTIPLY", "*"); np_btn(0, 3, "NUMPAD_MINUS", "-")
        np_btn(1, 0, "NUMPAD_7", "7"); np_btn(1, 1, "NUMPAD_8", "8"); np_btn(1, 2, "NUMPAD_9", "9"); np_btn(1, 3, "NUMPAD_PLUS", "+", h=84, rs=2)
        np_btn(2, 0, "NUMPAD_4", "4"); np_btn(2, 1, "NUMPAD_5", "5"); np_btn(2, 2, "NUMPAD_6", "6")
        np_btn(3, 0, "NUMPAD_1", "1"); np_btn(3, 1, "NUMPAD_2", "2"); np_btn(3, 2, "NUMPAD_3", "3"); np_btn(3, 3, "NUMPAD_ENTER", "Ent", h=84, rs=2)
        np_btn(4, 0, "NUMPAD_0", "0", w=114, cs=2); np_btn(4, 2, "NUMPAD_DOT", ".")

    def spacer(self, parent, w):
        ctk.CTkFrame(parent, width=w, height=1, fg_color="transparent").pack(side="left")

    def create_key(self, parent, code, current_key, w=55, h=40, text=None, text_size=11):
        if text is None: text = code
        is_selected = (code == current_key)
        btn = ctk.CTkButton(parent, text=text, width=w, height=h,
                          fg_color="#00CC66" if is_selected else "#2B2B2B",
                          hover_color="#00994D" if is_selected else "#3A3A3A",
                          text_color="white", font=("Arial", text_size, "bold"),
                          border_width=2 if is_selected else 1, border_color="#00CC66" if is_selected else "#444444",
                          command=lambda k=code: self.on_key_click(k))
        btn.pack(side="left", padx=2, pady=2)

    def on_key_click(self, key):
        self.callback(key)
        self.destroy()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DNF一键奔跑助手")
        self.geometry("450x600") 
        self.resizable(False, False)
        
        self.icon_on = create_dynamic_icon("icon_on.ico", "#00FF00", "circle")
        self.icon_off = create_dynamic_icon("icon_off.ico", "#666666", "rect")
        self.iconbitmap(self.icon_off)

        self.config = ConfigManager.load()
        # 使用原生API键盘
        self.kb = NativeKeyboard()
        self.logic = LogicThread(self.kb, self)
        
        self._apply_config_to_logic()
        self.logic.start()

        self._setup_ui()
        self._update_status_loop()

    def update_status_text(self, is_active):
        pass 

    def _apply_config_to_logic(self):
        self.logic.update_settings(self.config)

    def _save_and_update(self):
        ConfigManager.save(self.config)
        self._apply_config_to_logic()

    def _open_selector(self, config_key, title):
        current = self.config[config_key]
        KeySelectorWindow(self, title, current, lambda k: self._on_key_selected(config_key, k))

    def _on_key_selected(self, config_key, new_key):
        self.config[config_key] = new_key
        if config_key in self.btn_map:
            self.btn_map[config_key].configure(text=new_key)
        self._save_and_update()

    def toggle_from_logic(self, enabled):
        self.after(0, lambda: self._set_enabled(enabled))

    def _toggle_click(self):
        self._set_enabled(not self.logic.enabled)

    def _set_enabled(self, enabled):
        if self.logic.enabled == enabled: return 
        self.logic.enabled = enabled
        if enabled:
            play_mp3_native("on.mp3")
            self.iconbitmap(self.icon_on)
        else:
            play_mp3_native("off.mp3")
            self.iconbitmap(self.icon_off)
            self.logic.runner_left.force_stop()
            self.logic.runner_right.force_stop()
            self.logic.mapper_up.force_stop()
            self.logic.mapper_down.force_stop()
        self._update_ui_state()

    def _update_ui_state(self):
        if self.logic.enabled:
            if self.logic.game_active:
                self.status_lbl.configure(text="运行中", text_color="#00FF00")
            else:
                self.status_lbl.configure(text="运行中", text_color="#00FF00")
            self.btn_toggle.configure(text="停止脚本", fg_color="#FF3333")
        else:
            self.status_lbl.configure(text="已暂停", text_color="orange")
            self.btn_toggle.configure(text="启动脚本", fg_color="#00CC66")

    def _update_status_loop(self):
        self._update_ui_state()
        self.after(500, self._update_status_loop)

    def _setup_ui(self):
        ctk.CTkLabel(self, text="一键奔跑配置", font=("微软雅黑", 20, "bold")).pack(pady=15)

        status_frame = ctk.CTkFrame(self, fg_color="#222222")
        status_frame.pack(fill="x", padx=20, pady=5)
        self.status_lbl = ctk.CTkLabel(status_frame, text="初始化...", font=("微软雅黑", 14, "bold"))
        self.status_lbl.pack(pady=10)

        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.btn_map = {}

        header_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 5), padx=5)
        
        ctk.CTkLabel(header_frame, text="方向", width=50, font=("微软雅黑", 12, "bold"), text_color="gray").pack(side="left")
        ctk.CTkLabel(header_frame, text="物理按键", width=90, font=("微软雅黑", 12, "bold"), text_color="gray").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="", width=20).pack(side="left") 
        ctk.CTkLabel(header_frame, text="游戏按键", width=90, font=("微软雅黑", 12, "bold"), text_color="gray").pack(side="left", padx=5)

        ctk.CTkFrame(settings_frame, height=2, fg_color="#444444").pack(fill="x", pady=5, padx=10)

        def create_mapping_row(parent, label_text, trigger_key, output_key):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(row, text=label_text, width=50, anchor="center", font=("微软雅黑", 14, "bold")).pack(side="left")
            
            btn_trig = ctk.CTkButton(row, text=self.config[trigger_key], width=90, height=35,
                                     command=lambda: self._open_selector(trigger_key, f"设置 {label_text} [物理键]"))
            btn_trig.pack(side="left", padx=5)
            self.btn_map[trigger_key] = btn_trig
            
            ctk.CTkLabel(row, text="→", width=20, font=("Arial", 16), text_color="#666666").pack(side="left")
            
            btn_out = ctk.CTkButton(row, text=self.config[output_key], width=90, height=35, fg_color="#444444",
                                    hover_color="#555555",
                                    command=lambda: self._open_selector(output_key, f"设置 {label_text} [游戏内按键]"))
            btn_out.pack(side="left", padx=5)
            self.btn_map[output_key] = btn_out

        create_mapping_row(settings_frame, "上", "trigger_up", "output_up")
        create_mapping_row(settings_frame, "下", "trigger_down", "output_down")
        create_mapping_row(settings_frame, "左", "trigger_left", "output_left")
        create_mapping_row(settings_frame, "右", "trigger_right", "output_right")
        
        ctk.CTkFrame(settings_frame, height=2, fg_color="#444444").pack(fill="x", pady=15, padx=10)
        
        f = ctk.CTkFrame(settings_frame, fg_color="transparent")
        f.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(f, text="脚本暂停热键:", width=100, anchor="w", font=("微软雅黑", 12)).pack(side="left")
        btn = ctk.CTkButton(f, text=self.config["switch_key"], width=120, height=35,
                            command=lambda: self._open_selector("switch_key", "设置 暂停热键"))
        btn.pack(side="right")
        self.btn_map["switch_key"] = btn

        self.btn_toggle = ctk.CTkButton(self, text="启动脚本", height=50, font=("微软雅黑", 16, "bold"),
                                      command=self._toggle_click)
        self.btn_toggle.pack(fill="x", padx=20, pady=20, side="bottom")

    def on_closing(self):
        self.logic.running = False
        try:
            if os.path.exists("icon_on.ico"): os.remove("icon_on.ico")
            if os.path.exists("icon_off.ico"): os.remove("icon_off.ico")
        except: pass
        self.destroy()

if __name__ == "__main__":
    try:
        myappid = 'OneStepRun' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except: pass

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("尝试以管理员权限重启...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()