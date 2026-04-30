import ctypes
import json
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

user32 = ctypes.windll.user32
user32.VkKeyScanW.restype = ctypes.c_short
user32.VkKeyScanW.argtypes = [ctypes.c_wchar]


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

        key_str = str(param.get("key", "c"))
        key_code = self._key_to_code(key_str)

        w, h = context.controller.resolution
        cx, cy = w // 2, h // 2

        is_touching = False
        print(f"[MouseLongPress] 启动监听, 映射按键={key_str}(键码={key_code}), 目标({cx},{cy})")

        while not context.tasker.stopping:
            pressed = bool(user32.GetAsyncKeyState(key_code) & 0x8000)

            if pressed and not is_touching:
                context.controller.post_touch_down(cx, cy).wait()
                is_touching = True
            elif not pressed and is_touching:
                context.controller.post_touch_up().wait()
                is_touching = False

            time.sleep(0.01)

        if is_touching:
            context.controller.post_touch_up().wait()

        print("[MouseLongPress] 监听结束")
        return True