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
        recognition_detai = argv.reco_detail
        if recognition_detai.hit:
            context.controller.post_click(recognition_detai.box).wait()
            return True
        return False 
        


@AgentServer.custom_action("FocusEnergyAct")
class FocusEnergyAct(CustomAction):
    """聚能 - 点击聚能按钮坐标 (62, 633)"""
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("FocusEnergyAct: 点击聚能")
        context.controller.post_click(62, 633).wait()
        return True

@AgentServer.custom_action("AutoReleasePetAct")
class AutoReleasePetAction(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        recognition_detai = argv.reco_detail
        if recognition_detai.next_num:
            context.controller.post_click_key(recognition_detai.key_code).wait()
            return True
        return False

__all__ = [
    "AutoLaunchAct",
    "FocusEnergyAct",
    "AutoReleasePetAct"
]