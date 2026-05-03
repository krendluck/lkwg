"""
游戏基础动作模块

包含自动登录、聚能、自动放宠、鼠标长按映射四个 CustomAction。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
import ctypes
from ctypes import wintypes
import json
import time

user32 = ctypes.windll.user32
user32.VkKeyScanW.restype = ctypes.c_short
user32.VkKeyScanW.argtypes = [ctypes.c_wchar]

SW_RESTORE = 9

INPUT_MOUSE = 0
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT),
    ]


def _activate_game_window():
    hwnd = user32.FindWindowW(None, "洛克王国：世界")
    if not hwnd:
        hwnds = []

        def enum_callback(h, _):
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, title, 256)
            if "洛克" in title.value:
                hwnds.append(h)
            return True

        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(enum_callback)
        user32.EnumWindows(enum_proc, None)
        if hwnds:
            hwnd = hwnds[0]

    if hwnd:
        print(f"[Activate] 找到窗口 hwnd={hwnd}")
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
    else:
        print("[Activate] 未找到游戏窗口")

    return hwnd


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def _client_to_screen(hwnd, cx, cy):
    pt = POINT(cx, cy)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y


def _send_mouse_input(flags, sx, sy):
    ctypes.windll.user32.SetCursorPos(sx, sy)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.mi.dx = 0
    inp.mi.dy = 0
    inp.mi.mouseData = 0
    inp.mi.dwFlags = flags
    inp.mi.time = 0
    inp.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


@AgentServer.custom_action("AutoLaunchAct")
class AutoLaunchAct(CustomAction):
    """自动登录 - 点击识别到的登录按钮中心"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        reco_detail = argv.reco_detail
        if reco_detail is not None and reco_detail.hit:
            box = reco_detail.box
            if box:
                x = box[0] + box[2] // 2
                y = box[1] + box[3] // 2
                context.tasker.controller.post_click(x, y).wait()
                return True
        return False


@AgentServer.custom_action("FocusEnergyAct")
class FocusEnergyAct(CustomAction):
    """聚能 - 点击聚能按钮坐标 (62, 633)"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        context.tasker.controller.post_click(62, 633).wait()
        return True


@AgentServer.custom_action("AutoReleasePetAct")
class AutoReleasePetAct(CustomAction):
    """自动放宠 - 读取识别结果中的按键码并发送"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        reco_detail = argv.reco_detail
        if reco_detail is None or not reco_detail.hit:
            return False

        results = reco_detail.all_results
        if not results:
            return False

        detail = results[0].detail
        if not detail:
            return False

        next_num = detail.get("next_num")
        key_code = detail.get("key_code")
        if next_num is None:
            return False

        _activate_game_window()
        context.tasker.controller.post_click_key(key_code).wait()
        return True


@AgentServer.custom_action("MouseLongPress")
class MouseLongPressAction(CustomAction):

    @staticmethod
    def _key_to_code(key_str):
        if len(key_str) == 1:
            if key_str == ' ':
                return 0x20
            if key_str.isalnum():
                return user32.VkKeyScanW(key_str) & 0xFF
        return 50

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            param = json.loads(argv.custom_action_param or "{}")
        except Exception:
            param = {}

        key_str = str(param.get("key"))
        key_code = self._key_to_code(key_str)

        w, h = context.tasker.controller.resolution
        cx, cy = w // 2, h // 2

        is_touching = False
        print(f"[MouseLongPress] 启动监听, 映射按键={key_str}(键码={key_code}), 目标({cx},{cy})")

        hwnd = _activate_game_window()
        sx, sy = _client_to_screen(hwnd, cx, cy) if hwnd else (cx, cy)
        print(f"[MouseLongPress] 屏幕坐标 ({sx},{sy})")

        while not context.tasker.stopping:
            pressed = bool(user32.GetAsyncKeyState(key_code) & 0x8000)

            if pressed and not is_touching:
                print(f"[MouseLongPress] 按键按下 (键: {key_str})")
                _send_mouse_input(MOUSEEVENTF_LEFTDOWN, sx, sy)
                is_touching = True
            elif not pressed and is_touching:
                print(f"[MouseLongPress] 按键释放 (键: {key_str})")
                _send_mouse_input(MOUSEEVENTF_LEFTUP, sx, sy)
                is_touching = False

            time.sleep(0.05)

        if is_touching:
            _send_mouse_input(MOUSEEVENTF_LEFTUP, cx, cy)

        print("[MouseLongPress] 监听结束")
        return True


__all__ = [
    "AutoLaunchAct",
    "FocusEnergyAct",
    "AutoReleasePetAct",
    "MouseLongPressAction",
]
