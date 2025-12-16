import ctypes
import os
import time
import threading
import win32gui
from PIL import Image, ImageDraw
import pystray 

# =============================================================================
# 1. 驱动加载 
# =============================================================================
KEYBOARD_DLL_NAME = "logitech.driver.dll" 

class LogitechKeyboard:
    def __init__(self):
        self.driver = None
        self.ok = False
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.getcwd() 
        dll_path = os.path.join(base_path, KEYBOARD_DLL_NAME)
        if not os.path.exists(dll_path):
             dll_path = os.path.join(os.getcwd(), KEYBOARD_DLL_NAME)

        if os.path.exists(dll_path):
            try:
                self.driver = ctypes.CDLL(dll_path)
                if hasattr(self.driver, 'key_down'): self.driver.key_down.argtypes = [ctypes.c_char_p]
                if hasattr(self.driver, 'key_up'): self.driver.key_up.argtypes = [ctypes.c_char_p]
                if hasattr(self.driver, 'device_open'): self.driver.device_open()
                self.ok = True
            except: pass
        self.KEY_MAP = {'LEFT': b'left', 'RIGHT': b'right'}

    def press(self, key):
        if self.ok: self.driver.key_down(self.KEY_MAP[key])
    def release(self, key):
        if self.ok: self.driver.key_up(self.KEY_MAP[key])

# =============================================================================
# 2. 核心逻辑 
# =============================================================================
def is_physically_down(vk_code):
    return (ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000) != 0

class SafeRunner:
    def __init__(self, kb, direction_name, vk_code, other_runner=None):
        self.kb = kb
        self.key = direction_name
        self.vk = vk_code
        self.state = "IDLE" 
        self.other_runner = other_runner

    def force_stop(self):
        if self.state != "IDLE":
            self.kb.release(self.key)
            self.state = "IDLE"

    def process(self):
        phys_down = is_physically_down(self.vk)
        if not phys_down:
            if self.state != "IDLE":
                self.force_stop()
            return
        if self.state == "IDLE":
            if self.other_runner and self.other_runner.state != "IDLE":
                self.other_runner.force_stop()
            self.state = "STARTING"
            self.kb.press(self.key)
            time.sleep(0.015) 
            self.kb.release(self.key)
            time.sleep(0.015) 
            self.kb.press(self.key)
            self.state = "RUNNING"

def is_game_active():
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        if "地下城" in title or "DNF" in title or "WeGame" in title: 
            return True
        return False
    except: return False

# =============================================================================
# 3. MP3 播放逻辑 
# =============================================================================
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_F1 = 0x70

APP_RUNNING = True 
MACRO_ENABLED = True 
icon = None 
ICON_ON = None
ICON_OFF = None

def get_resource_path(filename):
    """获取外部文件的绝对路径 (兼容打包和脚本运行)"""
    # 注意：MP3文件不建议打包进exe内部，建议放在exe旁边，方便随时替换
    base_path = os.getcwd() 
    return os.path.join(base_path, filename)

def play_mp3_native(filename):
    
    file_path = get_resource_path(filename)
    
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

    
    threading.Thread(target=_worker, daemon=True).start()

def create_image(color_hex):
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), color=color_hex)
    dc = ImageDraw.Draw(image)
    dc.rectangle([16, 16, 48, 48], fill="white")
    dc.rectangle([22, 22, 42, 42], fill=color_hex)
    return image

def update_icon_state(is_enabled):
    global icon, ICON_ON, ICON_OFF
    if icon:
        if is_enabled:
            icon.icon = ICON_ON
            icon.title = "DNF助手: [开启]"
        else:
            icon.icon = ICON_OFF
            icon.title = "DNF助手: [暂停]"

def macro_loop():
    global MACRO_ENABLED, APP_RUNNING
    
    kb = LogitechKeyboard()

    runner_left = SafeRunner(kb, 'LEFT', VK_LEFT)
    runner_right = SafeRunner(kb, 'RIGHT', VK_RIGHT)
    runner_left.other_runner = runner_right
    runner_right.other_runner = runner_left

    last_f1 = False
    was_in_game = True 

    update_icon_state(True)

    while APP_RUNNING:
        try:
            # --- F1 开关逻辑 ---
            curr_f1 = is_physically_down(VK_F1)
            if curr_f1 and not last_f1:
                MACRO_ENABLED = not MACRO_ENABLED
                
                if MACRO_ENABLED:
                    # *** 播放 on.mp3 ***
                    play_mp3_native("on.mp3")
                    update_icon_state(True)
                else:
                    # *** 播放 off.mp3 ***
                    play_mp3_native("off.mp3")
                    update_icon_state(False)
                    runner_left.force_stop()
                    runner_right.force_stop()
            last_f1 = curr_f1

            if not MACRO_ENABLED:
                time.sleep(0.1)
                continue
            
            if not is_game_active():
                if was_in_game:
                    runner_left.force_stop()
                    runner_right.force_stop()
                    was_in_game = False
                time.sleep(0.5) 
                continue
            else:
                if not was_in_game:
                    was_in_game = True

            if kb.ok:
                runner_left.process()
                runner_right.process()
            
            time.sleep(0.001) 

        except Exception:
            time.sleep(1)

def on_quit(icon, item):
    global APP_RUNNING
    APP_RUNNING = False
    icon.stop()

def main():
    global icon, ICON_ON, ICON_OFF
    
    ICON_ON = create_image("#0078D7") 
    ICON_OFF = create_image("#555555") 

    t = threading.Thread(target=macro_loop, daemon=True)
    t.start()
    
    menu = pystray.Menu(pystray.MenuItem('退出', on_quit))
    icon = pystray.Icon("DNFAssist", ICON_ON, "初始化...", menu)
    
    if not ctypes.windll.shell32.IsUserAnAdmin():
         icon.title = "警告: 无管理员权限"

    icon.run()

if __name__ == "__main__":
    main()