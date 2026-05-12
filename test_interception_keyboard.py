"""
Interception 驱动键盘输入测试

目标窗口: 洛克王国：世界

此脚本使用 Interception 内核驱动发送底层扫描码击键，
绕过游戏 RawInput 输入保护。

使用方法:
  1. 确保 Interception 驱动已安装并重启电脑
  2. 打开游戏窗口
  3. 运行此脚本: python test_interception_keyboard.py
  4. 脚本会请求你先按一次任意键（驱动需要识别键盘设备）
  5. 然后自动发送测试按键到游戏窗口

注意: Interception 驱动在发送按键前必须先接收至少一次真实击键
      来确定键盘设备 ID。这是驱动的固有设计限制。
"""

import ctypes
import ctypes.wintypes
import time
import sys
import os
import threading

DLL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets", "resource", "base", "Dll", "interception.dll"
)

INTERCEPTION_MAX_DEVICE = 20

INTERCEPTION_KEY_DOWN = 0x00
INTERCEPTION_KEY_UP = 0x01
INTERCEPTION_KEY_E0 = 0x02
INTERCEPTION_KEY_E1 = 0x04

INTERCEPTION_FILTER_KEY_ALL = 0xFFFF
INTERCEPTION_FILTER_KEY_DOWN = INTERCEPTION_KEY_UP
INTERCEPTION_FILTER_KEY_UP = INTERCEPTION_KEY_UP << 1

INTERCEPTION_FILTER_MOUSE_ALL = 0xFFFF

INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN = 0x001
INTERCEPTION_MOUSE_LEFT_BUTTON_UP = 0x002
INTERCEPTION_MOUSE_MOVE_RELATIVE = 0x000

SCANCODE_MAP = {
    "ESC": 0x01,
    "1": 0x02,
    "2": 0x03,
    "3": 0x04,
    "4": 0x05,
    "5": 0x06,
    "6": 0x07,
    "7": 0x08,
    "8": 0x09,
    "9": 0x0A,
    "0": 0x0B,
    "Minus": 0x0C,
    "Equals": 0x0D,
    "Backspace": 0x0E,
    "Tab": 0x0F,
    "Q": 0x10,
    "W": 0x11,
    "E": 0x12,
    "R": 0x13,
    "T": 0x14,
    "Y": 0x15,
    "U": 0x16,
    "I": 0x17,
    "O": 0x18,
    "P": 0x19,
    "LeftBracket": 0x1A,
    "RightBracket": 0x1B,
    "Enter": 0x1C,
    "LeftCtrl": 0x1D,
    "A": 0x1E,
    "S": 0x1F,
    "D": 0x20,
    "F": 0x21,
    "G": 0x22,
    "H": 0x23,
    "J": 0x24,
    "K": 0x25,
    "L": 0x26,
    "Semicolon": 0x27,
    "Apostrophe": 0x28,
    "Grave": 0x29,
    "LeftShift": 0x2A,
    "Backslash": 0x2B,
    "Z": 0x2C,
    "X": 0x2D,
    "C": 0x2E,
    "V": 0x2F,
    "B": 0x30,
    "N": 0x31,
    "M": 0x32,
    "Comma": 0x33,
    "Period": 0x34,
    "Slash": 0x35,
    "RightShift": 0x36,
    "LeftAlt": 0x38,
    "Space": 0x39,
    "CapsLock": 0x3A,
    "F1": 0x3B,
    "F2": 0x3C,
    "F3": 0x3D,
    "F4": 0x3E,
    "F5": 0x3F,
    "F6": 0x40,
    "F7": 0x41,
    "F8": 0x42,
    "F9": 0x43,
    "F10": 0x44,
    "F11": 0x57,
    "F12": 0x58,
    "NumpadAdd": 0x4E,
    "Up": 0x48,
    "Down": 0x50,
    "Left": 0x4B,
    "Right": 0x4D,
    "Insert": 0x52,
    "Delete": 0x53,
    "Home": 0x47,
    "End": 0x4F,
    "PageUp": 0x49,
    "PageDown": 0x51,
}

EXTENDED_KEYS = {
    "Up", "Down", "Left", "Right",
    "Insert", "Delete", "Home", "End", "PageUp", "PageDown",
    "LeftCtrl", "RightCtrl",
    "LeftAlt", "RightAlt",
    "NumpadAdd",
}


class KeyStroke(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("state", ctypes.c_ushort),
        ("information", ctypes.c_uint),
    ]


class MouseStroke(ctypes.Structure):
    _fields_ = [
        ("state", ctypes.c_ushort),
        ("flags", ctypes.c_ushort),
        ("rolling", ctypes.c_short),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("information", ctypes.c_uint),
    ]


class Interception:
    def __init__(self, dll_path):
        self.dll = ctypes.CDLL(dll_path)
        self._setup_api()
        self.context = None
        self.keyboard_device = None
        self._callback_thread = None
        self._running = False
        self._filter_set = False

    def _setup_api(self):
        self.dll.interception_create_context.restype = ctypes.c_void_p
        self.dll.interception_create_context.argtypes = []

        self.dll.interception_destroy_context.restype = None
        self.dll.interception_destroy_context.argtypes = [ctypes.c_void_p]

        self.IS_KEYBOARD_CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)(
            self.dll.interception_is_keyboard
        )
        self.IS_MOUSE_CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)(
            self.dll.interception_is_mouse
        )

        self.dll.interception_set_filter.restype = None
        self.dll.interception_set_filter.argtypes = [
            ctypes.c_void_p,
            ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int),
            ctypes.c_ushort,
        ]

        self.dll.interception_wait.restype = ctypes.c_int
        self.dll.interception_wait.argtypes = [ctypes.c_void_p]

        self.dll.interception_wait_with_timeout.restype = ctypes.c_int
        self.dll.interception_wait_with_timeout.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

        self.dll.interception_send.restype = ctypes.c_int
        self.dll.interception_send.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(KeyStroke), ctypes.c_uint
        ]

        self.dll.interception_receive.restype = ctypes.c_int
        self.dll.interception_receive.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(KeyStroke), ctypes.c_uint
        ]

        self.dll.interception_is_keyboard.restype = ctypes.c_int
        self.dll.interception_is_keyboard.argtypes = [ctypes.c_int]

        self.dll.interception_is_mouse.restype = ctypes.c_int
        self.dll.interception_is_mouse.argtypes = [ctypes.c_int]

        self.dll.interception_is_invalid.restype = ctypes.c_int
        self.dll.interception_is_invalid.argtypes = [ctypes.c_int]

        self.dll.interception_get_hardware_id.restype = ctypes.c_uint
        self.dll.interception_get_hardware_id.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint
        ]

    def create_context(self):
        self.context = self.dll.interception_create_context()
        if not self.context:
            raise RuntimeError("Failed to create Interception context. Is the driver installed?")
        return self.context

    def destroy_context(self):
        if self.context:
            self.dll.interception_destroy_context(self.context)
            self.context = None

    def set_keyboard_filter(self, filter_mode=INTERCEPTION_FILTER_KEY_ALL):
        self.dll.interception_set_filter(
            self.context, self.IS_KEYBOARD_CB, filter_mode
        )
        self._filter_set = True

    def set_mouse_filter(self, filter_mode=INTERCEPTION_FILTER_MOUSE_ALL):
        self.dll.interception_set_filter(
            self.context, self.IS_MOUSE_CB, filter_mode
        )

    def wait(self):
        return self.dll.interception_wait(self.context)

    def wait_with_timeout(self, milliseconds):
        return self.dll.interception_wait_with_timeout(self.context, milliseconds)

    def send_key(self, device, code, state=INTERCEPTION_KEY_DOWN, information=0):
        stroke = KeyStroke()
        stroke.code = code
        stroke.state = state
        stroke.information = information
        return self.dll.interception_send(self.context, device, ctypes.byref(stroke), 1)

    def receive_key(self, device):
        stroke = KeyStroke()
        result = self.dll.interception_receive(self.context, device, ctypes.byref(stroke), 1)
        return stroke, result

    def is_keyboard(self, device):
        return self.dll.interception_is_keyboard(device) > 0

    def is_mouse(self, device):
        return self.dll.interception_is_mouse(device) > 0

    def is_invalid(self, device):
        return self.dll.interception_is_invalid(device) > 0

    def get_hardware_id(self, device, size=512):
        buf = ctypes.create_string_buffer(size)
        self.dll.interception_get_hardware_id(self.context, device, buf, size)
        return buf.value.decode("utf-8", errors="replace")

    def discover_keyboard_device(self, timeout_ms=15000):
        if not self._filter_set:
            self.set_keyboard_filter(INTERCEPTION_FILTER_KEY_ALL)

        print("[Interception] 等待键盘输入来识别键盘设备...")
        print("[Interception] 请按任意键（输入将被拦截并转发，不会丢失）...")
        print(f"[Interception] 等待超时: {timeout_ms / 1000:.0f}秒\n")

        start_time = time.time()
        keyboard_found = False

        while True:
            elapsed = (time.time() - start_time) * 1000
            remaining = int(timeout_ms - elapsed)
            if remaining <= 0:
                break

            device = self.dll.interception_wait_with_timeout(self.context, min(remaining, 3000))
            if self.is_invalid(device):
                continue

            if self.is_keyboard(device):
                self.keyboard_device = device
                try:
                    hw_id = self.get_hardware_id(device)
                except Exception:
                    hw_id = "(unknown)"
                print(f"[Interception] 检测到键盘设备: device={device}, hardware_id=\"{hw_id}\"")

                stroke, result = self.receive_key(device)
                self.dll.interception_send(self.context, device, ctypes.byref(stroke), 1)
                print(f"[Interception] 首次按键已转发: scancode=0x{stroke.code:02X}, state={stroke.state}")
                keyboard_found = True
                break
            else:
                stroke, result = self.receive_key(device)
                self.dll.interception_send(self.context, device, ctypes.byref(stroke), 1)
                print(f"[Interception] 忽略非键盘设备事件 device={device}")

        if not keyboard_found:
            print("[Interception] 等待超时，未检测到键盘输入！")
            print("[Interception] 请确保:")
            print("  1. Interception 驱动已正确安装")
            print("  2. 已重启电脑")
            print("  3. 脚本以管理员权限运行")
            return False

        print(f"[Interception] 键盘设备ID: {self.keyboard_device}\n")
        return True

    def _passthrough_loop(self):
        while self._running:
            try:
                device = self.dll.interception_wait_with_timeout(self.context, 200)
                if self.is_invalid(device):
                    continue

                if self.is_keyboard(device):
                    stroke = KeyStroke()
                    result = self.dll.interception_receive(
                        self.context, device, ctypes.byref(stroke), 1
                    )
                    if result > 0:
                        self.dll.interception_send(
                            self.context, device, ctypes.byref(stroke), 1
                        )
                elif self.is_mouse(device):
                    stroke = MouseStroke()
                    result = self.dll.interception_receive(
                        self.context, device, ctypes.byref(stroke), 1
                    )
                    if result > 0:
                        self.dll.interception_send(
                            self.context, device, ctypes.byref(stroke), 1
                        )
                else:
                    stroke = KeyStroke()
                    result = self.dll.interception_receive(
                        self.context, device, ctypes.byref(stroke), 1
                    )
                    if result > 0:
                        self.dll.interception_send(
                            self.context, device, ctypes.byref(stroke), 1
                        )
            except Exception as e:
                if self._running:
                    print(f"[Interception] 透传线程异常: {e}")
                break

    def start_passthrough(self):
        if self._callback_thread and self._callback_thread.is_alive():
            return
        self.set_keyboard_filter(INTERCEPTION_FILTER_KEY_ALL)
        self._running = True
        self._callback_thread = threading.Thread(target=self._passthrough_loop, daemon=True)
        self._callback_thread.start()

    def stop_passthrough(self):
        self._running = False
        if self._callback_thread:
            self._callback_thread.join(timeout=2)

    def click_key(self, scancode, extended=False, delay=0.05):
        if self.keyboard_device is None:
            raise RuntimeError("Keyboard device not discovered. Call discover_keyboard_device() first.")

        e0_flag = INTERCEPTION_KEY_E0 if extended else 0
        self.send_key(self.keyboard_device, scancode, INTERCEPTION_KEY_DOWN | e0_flag)
        time.sleep(delay)
        self.send_key(self.keyboard_device, scancode, INTERCEPTION_KEY_UP | e0_flag)
        time.sleep(delay)

    def click_key_by_name(self, name, delay=0.05):
        if name not in SCANCODE_MAP:
            print(f"[Warn] 未知按键: {name}")
            return False
        scancode = SCANCODE_MAP[name]
        extended = name in EXTENDED_KEYS
        self.click_key(scancode, extended=extended, delay=delay)
        return True


def find_window_by_title(title_substring):
    user32 = ctypes.windll.user32
    result = []

    def enum_callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if title_substring in buf.value:
                    result.append((hwnd, buf.value))

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return result


SW_RESTORE = 9


def activate_window(hwnd):
    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.1)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)


def list_all_devices(interp):
    print("[Interception] 扫描所有设备:")
    found_any = False
    for i in range(1, INTERCEPTION_MAX_DEVICE + 1):
        if interp.is_keyboard(i):
            try:
                hw_id = interp.get_hardware_id(i)
            except Exception:
                hw_id = "(error)"
            if hw_id:
                print(f"  键盘 device={i}: \"{hw_id}\"")
                found_any = True
        elif interp.is_mouse(i):
            try:
                hw_id = interp.get_hardware_id(i)
            except Exception:
                hw_id = "(error)"
            if hw_id:
                print(f"  鼠标 device={i}: \"{hw_id}\"")
                found_any = True
    if not found_any:
        print("  未发现任何设备（需要设置 filter 后才能枚举）")
    print()


def main():
    window_title = "洛克王国：世界"

    print("=" * 60)
    print("  Interception 驱动键盘测试")
    print("  目标窗口: " + window_title)
    print("=" * 60)

    windows = find_window_by_title(window_title)
    if not windows:
        print(f"\n警告: 未找到包含 \"{window_title}\" 的窗口！")
        print("测试仍将继续，但请打开游戏窗口以验证效果。")
    else:
        hwnd, title = windows[0]
        print(f"\n找到窗口: hwnd={hwnd} title=\"{title}\"")

    if not os.path.exists(DLL_PATH):
        print(f"\n错误: 找不到 interception.dll: {DLL_PATH}")
        sys.exit(1)

    print(f"\n加载 interception.dll: {DLL_PATH}")
    interp = Interception(DLL_PATH)

    print("创建 Interception 上下文...")
    try:
        interp.create_context()
        print(f"上下文创建成功: 0x{interp.context:X}")
    except RuntimeError as e:
        print(f"\n错误: {e}")
        print("\n可能原因:")
        print("  1. Interception 驱动未安装")
        print("  2. 安装后未重启电脑")
        print("  3. 需要管理员权限运行")
        sys.exit(1)

    print("\n-" * 60)
    print("  重要: 脚本将拦截键盘输入!")
    print("  在发现键盘设备之前，你的键盘输入将被暂时捕获。")
    print("  按一次任意键后，脚本会转发所有输入并开始测试。")
    print("-" * 60)

    print("\n>>> 请现在按一次任意键来让驱动识别键盘设备 <<<\n")

    if not interp.discover_keyboard_device(timeout_ms=20000):
        print("\n未能发现键盘设备，退出。")
        interp.destroy_context()
        sys.exit(1)

    print("键盘设备已发现，启动键盘透传线程...")
    interp.start_passthrough()
    print("键盘透传线程已启动（你的键盘将正常工作）。\n")

    try:
        if windows:
            hwnd, title = windows[0]
            print(f"激活游戏窗口: \"{title}\"")
            activate_window(hwnd)

        test_keys = [
            ("W", "前进"),
            ("1", "数字键1"),
            ("F", "互动/攻击"),
            ("ESC", "退出/取消"),
            ("Tab", "Tab切换"),
            ("F1", "功能键F1"),
            ("Space", "空格"),
            ("LeftShift", "左Shift"),
        ]

        print("\n" + "=" * 60)
        print("  开始 Interception 键盘测试")
        print("=" * 60)
        print(f"  将依次测试 {len(test_keys)} 个按键，每个间隔 1.5 秒")
        print("  请观察游戏窗口是否有反应！\n")
        print("  3 秒后开始...\n")
        time.sleep(3)

        for i, (name, desc) in enumerate(test_keys):
            print(f"  [{i+1}/{len(test_keys)}] 发送按键: {name} ({desc})")
            interp.click_key_by_name(name, delay=0.05)
            time.sleep(1.5)

        print("\n" + "=" * 60)
        print("  测试完成！")
        print("=" * 60)
        print("\n请报告结果:")
        for name, desc in test_keys:
            print(f"  {name:12s} ({desc}): 有效/无效")
        print()
        print("如果大多数按键有效，说明 Interception 驱动可以用于游戏键盘输入。")
        print("如果全部无效，可能需要在管理员模式下运行或检查驱动安装。")

    finally:
        print("\n正在清理 Interception 上下文...")
        interp.stop_passthrough()
        interp.destroy_context()
        print("已清理。")


if __name__ == "__main__":
    main()