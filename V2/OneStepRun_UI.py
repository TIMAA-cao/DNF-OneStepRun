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
# 0. 辅助功能：MP3 播放 & 资源路径
# =============================================================================

def get_real_path(filename):
    """
    获取文件的绝对路径，强制指向 EXE 所在的目录。
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包后的 EXE，使用 EXE 文件所在的目录
        application_path = os.path.dirname(sys.executable)
    else:
        # 如果是脚本运行，使用脚本所在的目录
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(application_path, filename)

def play_mp3_native(filename):
    # 强制去 EXE 旁边找 MP3
    file_path = get_real_path(filename)
    
    if not os.path.exists(file_path):
        return

    def _worker():
        
        alias = f"mp3_{int(time.time()*1000)}" 
        cmd_open = f'open "{file_path}" type mpegvideo alias {alias}'
        cmd_play = f'play {alias} wait' 
        cmd_close = f'close {alias}'
        
        mci = ctypes.windll.winmm.mciSendStringW
        mci(cmd_open, None, 0, 0)
        mci(cmd_play, None, 0, 0)
        mci(cmd_close, None, 0, 0)
    
    # 启动独立线程播放，防止卡顿
    threading.Thread(target=_worker, daemon=True).start()

def create_dynamic_icon(filename, color_hex, shape="rect"):
    
    size = (64, 64)
    # 创建透明背景图像
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 画边框和填充
    if shape == "circle":
        # 绿色圆形 (运行中)
        draw.ellipse((4, 4, 60, 60), fill=color_hex, outline="white", width=3)
        # 画一个简易的播放三角形
        draw.polygon([(24, 16), (24, 48), (48, 32)], fill="white")
    else:
        # 灰色圆角矩形 (暂停)
        draw.rounded_rectangle((4, 4, 60, 60), radius=10, fill=color_hex, outline="white", width=3)
        # 画一个简易的暂停双竖线
        draw.rectangle((22, 18, 28, 46), fill="white")
        draw.rectangle((36, 18, 42, 46), fill="white")
    
    # 图标生成在 EXE 旁边
    icon_path = get_real_path(filename)
    image.save(icon_path, format="ICO")
    return icon_path

# =============================================================================
# 1. 全局配置与按键映射表
# =============================================================================
CONFIG_FILE = "run_config.json"

VK_MAP = {
    # 鼠标
    'LBUTTON': 0x01, 'RBUTTON': 0x02, 'MBUTTON': 0x04,
    
    # 控制键
    'BACKSPACE': 0x08, 'TAB': 0x09, 'CLEAR': 0x0C, 'ENTER': 0x0D,
    'SFT': 0x10, 'CTL': 0x11, 'ALT': 0x12, 'PAUSE': 0x13, 'CAPS': 0x14, 
    'ESC': 0x1B, 'SPACE': 0x20, 
    'LWIN': 0x5B, 'RWIN': 0x5C, 'APPS': 0x5D,
    'LSHIFT': 0xA0, 'RSHIFT': 0xA1, 'LCONTROL': 0xA2, 'RCONTROL': 0xA3, 'LALT': 0xA4, 'RALT': 0xA5,
    'PRINTSCREEN': 0x2C, 'SCROLLLOCK': 0x91, 'NUMLOCK': 0x90,

    # 导航键
    'PAGEUP': 0x21, 'PAGEDOWN': 0x22, 'END': 0x23, 'HOME': 0x24, 
    'LEFT': 0x25, 'UP': 0x26, 'RIGHT': 0x27, 'DOWN': 0x28,
    'INSERT': 0x2D, 'DELETE': 0x2E,

    # 数字行
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,

    # 字母
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46, 'G': 0x47,
    'H': 0x48, 'I': 0x49, 'J': 0x4A, 'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E,
    'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54, 'U': 0x55,
    'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A,

    # 小键盘
    'NUMPAD_0': 0x60, 'NUMPAD_1': 0x61, 'NUMPAD_2': 0x62, 'NUMPAD_3': 0x63,
    'NUMPAD_4': 0x64, 'NUMPAD_5': 0x65, 'NUMPAD_6': 0x66, 'NUMPAD_7': 0x67,
    'NUMPAD_8': 0x68, 'NUMPAD_9': 0x69, 
    'NUMPAD_MULTIPLY': 0x6A, 'NUMPAD_PLUS': 0x6B, 'NUMPAD_MINUS': 0x6D, 
    'NUMPAD_DOT': 0x6E, 'NUMPAD_DIVIDE': 0x6F, 'NUMPAD_ENTER': 0x0D,

    # 功能键
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74, 'F6': 0x75,
    'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,

    # 符号
    'SEMICOLON': 0xBA, 'EQUAL': 0xBB, 'COMMA': 0xBC, 'MINUS': 0xBD, 'PERIOD': 0xBE,
    'SLASH': 0xBF, 'GRAVE': 0xC0, 'LBRACKET': 0xDB, 'BACKSLASH': 0xDC, 'RBRACKET': 0xDD, 'QUOTE': 0xDE
}

class ConfigManager:
    DEFAULT_CONFIG = {
        "trigger_left": "LEFT",       
        "trigger_right": "RIGHT",     
        "output_left": "GAME_LEFT",   
        "output_right": "GAME_RIGHT", 
        "switch_key": "F12"           
    }

    @staticmethod
    def load():
        # 从 EXE 旁边读取配置
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
            # 保存到 EXE 旁边
            path = get_real_path(CONFIG_FILE)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")

# =============================================================================
# 2. 驱动加载 (Logitech)
# =============================================================================
KEYBOARD_DLL_NAME = "logitech.driver.dll" 

class LogitechKeyboard:
    def __init__(self):
        self.driver = None
        self.ok = False
        self.KEY_MAP = {}
        self._load_driver()
        self._init_key_map()

    def _load_driver(self):
        # 【关键修改】强制去 EXE 所在目录找 DLL
        dll_path = get_real_path(KEYBOARD_DLL_NAME)
        
        if os.path.exists(dll_path):
            try:
                self.driver = ctypes.CDLL(dll_path)
                if hasattr(self.driver, 'key_down'): self.driver.key_down.argtypes = [ctypes.c_char_p]
                if hasattr(self.driver, 'key_up'): self.driver.key_up.argtypes = [ctypes.c_char_p]
                if hasattr(self.driver, 'device_open'): self.driver.device_open()
                self.ok = True
            except Exception as e:
                pass
        else:
            # print(f"未找到驱动文件: {dll_path}")
            pass

    def _init_key_map(self):
        base_map = {
            'A': b'a', 'B': b'b', 'C': b'c', 'D': b'd', 'E': b'e', 'F': b'f', 'G': b'g', 
            'H': b'h', 'I': b'i', 'J': b'j', 'K': b'k', 'L': b'l', 'M': b'm', 'N': b'n', 
            'O': b'o', 'P': b'p', 'Q': b'q', 'R': b'r', 'S': b's', 'T': b't', 'U': b'u', 
            'V': b'v', 'W': b'w', 'X': b'x', 'Y': b'y', 'Z': b'z',
            '0': b'0', '1': b'1', '2': b'2', '3': b'3', '4': b'4', '5': b'5', 
            '6': b'6', '7': b'7', '8': b'8', '9': b'9',
            'LEFT': b'left', 'RIGHT': b'right', 'UP': b'up', 'DOWN': b'down',
            'SPACE': b'space', 'ENTER': b'enter', 'ESC': b'esc', 'TAB': b'tab',
            'ALT': b'lalt', 'R_ALT': b'ralt', 'CTL': b'lctrl', 'SFT': b'lshift',
            'F1': b'f1', 'F12': b'f12'
        }
        self.KEY_MAP = base_map

    def update_game_keys(self, left_key_name, right_key_name):
        code_left = self.KEY_MAP.get(left_key_name)
        code_right = self.KEY_MAP.get(right_key_name)
        if code_left: self.KEY_MAP['GAME_LEFT'] = code_left
        if code_right: self.KEY_MAP['GAME_RIGHT'] = code_right

    def press(self, key):
        if self.ok and key in self.KEY_MAP: 
            self.driver.key_down(self.KEY_MAP[key])
    def release(self, key):
        if self.ok and key in self.KEY_MAP: 
            self.driver.key_up(self.KEY_MAP[key])

# =============================================================================
# 3. 核心逻辑 (SafeRunner - 修复奔跑不稳的问题)
# =============================================================================
def is_physically_down(vk_code):
    if vk_code is None: return False
    return (ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000) != 0

class SafeRunner:
    def __init__(self, kb, output_key_name, trigger_vk_code, other_runner=None):
        self.kb = kb
        self.output_key = output_key_name 
        self.trigger_vk = trigger_vk_code 
        self.state = "IDLE" 
        self.other_runner = other_runner
        self.press_time = 0.0      
        self.was_phys_down = False 

    def update_config(self, output_key_name, trigger_vk_code):
        self.output_key = output_key_name
        self.trigger_vk = trigger_vk_code

    def force_stop(self):
        if self.state != "IDLE":
            self.kb.release(self.output_key)
            self.state = "IDLE"

    def process(self):
        phys_down = is_physically_down(self.trigger_vk)
        
        # 记录按下时间戳
        if phys_down and not self.was_phys_down:
            self.press_time = time.time()
        self.was_phys_down = phys_down
        
        # 双键冲突裁决
        if phys_down:
            if self.other_runner and self.other_runner.was_phys_down:
                if self.press_time < self.other_runner.press_time:
                    self.force_stop()
                    return 

        # 状态机
        if phys_down:
            if self.state == "IDLE":
                if self.other_runner:
                    self.other_runner.force_stop()
                
                self.state = "RUNNING"
                
                # --- 奔跑---
                # 1. 第一次按下
                self.kb.press(self.output_key) 
                time.sleep(0.02)  # 【修复】增加到 20ms，防止太快服务器没读到
                
                # 2. 松开 (制造间隔)
                self.kb.release(self.output_key)
                time.sleep(0.04)  # 【修复】增加到 40ms，确保服务器识别为“双击”
                
                # 3. 第二次按下并保持
                self.kb.press(self.output_key)
                # print(f"奔跑触发: {self.output_key}")
                
            elif self.state == "RUNNING":
                pass
        else:
            if self.state == "RUNNING":
                self.kb.release(self.output_key)
                self.state = "IDLE"

# =============================================================================
# 4. 后台逻辑线程 (修复音效)
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
        
        self.current_switch_vk = 0
        self.last_switch_state = False
        self.game_active = False 

    def update_settings(self, config):
        trigger_l = config['trigger_left']
        trigger_r = config['trigger_right']
        vk_l = VK_MAP.get(trigger_l, 0)
        vk_r = VK_MAP.get(trigger_r, 0)
        
        self.runner_left.update_config('GAME_LEFT', vk_l)
        self.runner_right.update_config('GAME_RIGHT', vk_r)
        self.current_switch_vk = VK_MAP.get(config['switch_key'], 0)

    def run(self):
        while self.running:
            # --- 全局快捷键开关检测 ---
            if self.current_switch_vk:
                curr_sw = is_physically_down(self.current_switch_vk)
                if curr_sw and not self.last_switch_state:
                    # 调用UI回调进行切换
                    self.app_ref.toggle_from_logic(not self.enabled)
                self.last_switch_state = curr_sw

            # 2. 窗口活跃检测
            self.game_active = self._is_game_active()

            # 3. 执行逻辑
            if self.enabled and self.kb.ok:
                if self.game_active:
                    self.runner_left.process()
                    self.runner_right.process()
                else:
                    if self.runner_left.state != "IDLE": self.runner_left.force_stop()
                    if self.runner_right.state != "IDLE": self.runner_right.force_stop()
            
            time.sleep(0.001)

    def _is_game_active(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd: return False 
            title = win32gui.GetWindowText(hwnd)
            if "地下城" in title or "DNF" in title or "WeGame" in title: 
                return True
            return False
        except: return True 

# =============================================================================
# 5. UI : 键盘选择器 & 主窗口
# =============================================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class KeySelectorWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_key, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("请选择按键")
        
        self.geometry("1450x550")
        self.minsize(1000, 400)
        self.attributes("-topmost", True)
        self.grab_set() 
        
        try:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width - 1450) // 2
            y = (screen_height - 600) // 2
            self.geometry(f"+{x}+{y}")
        except: pass

        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a")
        self.scroll_container.pack(fill="both", expand=True)
        
        self.content_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.content_frame.pack(anchor="center", pady=40, padx=20)

        self._setup_keyboard_layout(current_key)
        
        self.lift()
        self.focus_force()

    def _setup_keyboard_layout(self, current_key):
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

        # Nav & Arrows
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

        # Numpad
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
        self.title("DNF一键奔跑助手 (Pro)")
        self.geometry("400x520")
        self.resizable(False, False)
        
        # 0. 初始化图标文件 
        self.icon_on = create_dynamic_icon("icon_on.ico", "#00FF00", "circle")
        self.icon_off = create_dynamic_icon("icon_off.ico", "#666666", "rect")
        
        # 设置默认图标（灰）
        self.iconbitmap(self.icon_off)

        self.config = ConfigManager.load()
        self.kb = LogitechKeyboard()
        # 将 self 传入逻辑线程，以便回调更新UI
        self.logic = LogicThread(self.kb, self)
        
        self._apply_config_to_logic()
        self.logic.start()

        self._setup_ui()
        self._update_status_loop()

    def _apply_config_to_logic(self):
        self.kb.update_game_keys(self.config['output_left'], self.config['output_right'])
        self.logic.update_settings(self.config)

    def _save_and_update(self):
        ConfigManager.save(self.config)
        self._apply_config_to_logic()

    def _open_selector(self, config_key):
        current = self.config[config_key]
        KeySelectorWindow(self, current, lambda k: self._on_key_selected(config_key, k))

    def _on_key_selected(self, config_key, new_key):
        self.config[config_key] = new_key
        self.btn_map[config_key].configure(text=new_key)
        self._save_and_update()

    def toggle_from_logic(self, enabled):
        
        self.after(0, lambda: self._set_enabled(enabled))

    def _toggle_click(self):
       
        self._set_enabled(not self.logic.enabled)

    def _set_enabled(self, enabled):
        """统一的状态切换入口"""
        if self.logic.enabled == enabled: return 
        
        self.logic.enabled = enabled
        
        if enabled:
            play_mp3_native("on.mp3")
            # 切换为绿色图标
            self.iconbitmap(self.icon_on)
        else:
            play_mp3_native("off.mp3")
            # 切换为灰色图标
            self.iconbitmap(self.icon_off)
            self.logic.runner_left.force_stop()
            self.logic.runner_right.force_stop()
            
        self._update_ui_state()

    def _update_ui_state(self):
        if self.logic.enabled:
            # 状态文字会根据是否在前台动态变化
            if self.logic.game_active:
                self.status_lbl.configure(text="运行中 (检测到游戏)", text_color="#00FF00")
            else:
                self.status_lbl.configure(text="运行中 (等待游戏窗口)", text_color="#FFFF00")
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

        def create_row(parent, label, conf_key):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", pady=8, padx=10)
            ctk.CTkLabel(f, text=label, width=100, anchor="w", font=("微软雅黑", 12)).pack(side="left")
            btn = ctk.CTkButton(f, text=self.config[conf_key], width=120, 
                                command=lambda: self._open_selector(conf_key))
            btn.pack(side="right")
            self.btn_map[conf_key] = btn

        create_row(settings_frame, "物理 左跑键:", "trigger_left")
        create_row(settings_frame, "物理 右跑键:", "trigger_right")
        
        ctk.CTkFrame(settings_frame, height=2, fg_color="gray").pack(fill="x", pady=10, padx=10)
        
        create_row(settings_frame, "游戏内 左移:", "output_left")
        create_row(settings_frame, "游戏内 右移:", "output_right")

        ctk.CTkFrame(settings_frame, height=2, fg_color="gray").pack(fill="x", pady=10, padx=10)
        
        create_row(settings_frame, "开关 快捷键:", "switch_key")

        self.btn_toggle = ctk.CTkButton(self, text="启动脚本", height=50, font=("微软雅黑", 16, "bold"),
                                      command=self._toggle_click)
        self.btn_toggle.pack(fill="x", padx=20, pady=20, side="bottom")

    def on_closing(self):
        self.logic.running = False
        # 清理临时图标文件
        try:
            if os.path.exists("icon_on.ico"): os.remove("icon_on.ico")
            if os.path.exists("icon_off.ico"): os.remove("icon_off.ico")
        except: pass
        self.destroy()

if __name__ == "__main__":
    
    try:
        myappid = 'mycompany.myproduct.subproduct.version' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except: pass

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("尝试以管理员权限重启...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()