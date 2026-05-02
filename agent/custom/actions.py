"""
游戏基础动作模块

包含自动登录和聚能两个简单 CustomAction。
这些动作通过 context.controller 直接操控游戏窗口（点击坐标）。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("AutoLaunchAct")
class AutoLaunchAct(CustomAction):
    """自动登录 - 点击登录按钮坐标 (640, 538)"""
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("AutoLaunchAct: 点击登录按钮")
        context.controller.post_click(640, 538).wait()
        return True


@AgentServer.custom_action("FocusEnergyAct")
class FocusEnergyAct(CustomAction):
    """聚能 - 点击聚能按钮坐标 (62, 633)"""
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("FocusEnergyAct: 点击聚能")
        context.controller.post_click(62, 633).wait()
        return True


__all__ = [
    "AutoLaunchAct",
    "FocusEnergyAct",
]