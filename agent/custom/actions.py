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
        reco_detail = argv.reco_detail
        if reco_detail is not None and reco_detail.hit:
            box = reco_detail.box
            if box:
                x = box[0] + box[2] // 2
                y = box[1] + box[3] // 2
                context.controller.post_click(x, y).wait()
                return True
        return False 
        


@AgentServer.custom_action("FocusEnergyAct")
class FocusEnergyAct(CustomAction):
    """聚能 - 点击聚能按钮坐标 (62, 633)"""
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("FocusEnergyAct: 点击聚能")
        context.controller.post_click(62, 633).wait()
        return True

@AgentServer.custom_action("AutoReleasePetAction")
class AutoReleasePetAction(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        reco_detail = argv.reco_detail
        detail = {}
        if reco_detail is not None and isinstance(reco_detail.raw_detail, dict):
            detail = reco_detail.raw_detail

        key_code = detail.get("key_code", 50)
        next_num = detail.get("next_num")
        if next_num is not None:
            context.controller.post_click_key(key_code).wait()
            return True
        return False

__all__ = [
    "AutoLaunchAct",
    "FocusEnergyAct",
    "AutoReleasePetAction",
]