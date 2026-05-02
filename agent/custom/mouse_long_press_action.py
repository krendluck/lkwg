"""
鼠标长按映射模块

功能：监听物理键盘按键，当按键按下时在游戏画面中心持续触摸（按住不放），
      松开按键时抬起触摸。用于将键盘按键映射为游戏中的长按操作。

使用场景：游戏中需要长按屏幕某个位置，但用键盘按键来控制更方便。
  例如：按住键盘 C 键 → 游戏中持续触摸屏幕中心（用于移动/攻击等）

Pipeline 配置：
  MouseLongPressEntry (DirectHit) → MouseLongPress → [] (空next，持续循环直到任务停止)
  custom_action_param 示例: {"key": "c"}
"""

import ctypes
import json
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

# Windows API 调用，用于检测键盘按键状态
user32 = ctypes.windll.user32
user32.VkKeyScanW.restype = ctypes.c_short
user32.VkKeyScanW.argtypes = [ctypes.c_wchar]


@AgentServer.custom_action("MouseLongPress")
class MouseLongPressAction(CustomAction):

    @staticmethod
    def _key_to_code(key_str):
        """将单个字符转换为 Windows 虚拟键码

        Args:
            key_str: 单个字符，如 'c', 'a', '1', ' ' 等

        Returns:
            int: 对应的虚拟键码，无法识别时返回 50（数字键2）
        """
        if len(key_str) == 1:
            if key_str == ' ':
                return 0x20  # 空格键 VK_SPACE
            if key_str.isalnum():
                # VkKeyScanW 将字符转换为虚拟键码，& 0xFF 取低8位
                return user32.VkKeyScanW(key_str) & 0xFF
        return 50  # 默认数字键2

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 解析参数，获取要映射的按键字母，默认为 'c'
        try:
            param = json.loads(argv.custom_action_param or "{}")
        except Exception:
            param = {}

        key_str = str(param.get("key", "c"))
        key_code = self._key_to_code(key_str)

        # 获取游戏窗口分辨率，计算屏幕中心点用于触摸
        w, h = context.controller.resolution
        cx, cy = w // 2, h // 2

        is_touching = False
        print(f"[MouseLongPress] 启动监听, 映射按键={key_str}(键码={key_code}), 目标({cx},{cy})")

        # 持续循环：检测按键状态 → 同步触摸状态
        # context.tasker.stopping 为 True 时表示任务被中断，退出循环
        while not context.tasker.stopping:
            # GetAsyncKeyState 检测按键是否正在被按下，& 0x8000 取最高位
            pressed = bool(user32.GetAsyncKeyState(key_code) & 0x8000)

            if pressed and not is_touching:
                # 按键刚按下 → 触摸屏幕
                context.controller.post_touch_down(cx, cy).wait()
                is_touching = True
            elif not pressed and is_touching:
                # 按键刚松开 → 抬起触摸
                context.controller.post_touch_up().wait()
                is_touching = False

            time.sleep(0.01)  # 10ms 轮询间隔，避免占用过多 CPU

        # 退出时如果还在触摸中，确保抬起
        if is_touching:
            context.controller.post_touch_up().wait()

        print("[MouseLongPress] 监听结束")
        return True