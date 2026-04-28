from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("AutoLaunchAct")
class AutoLaunchAct(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("AutoLaunchAct: 点击登录按钮")
        context.controller.post_click(640, 538).wait()
        return True


@AgentServer.custom_action("LaunchCheckAct")
class LaunchCheckAct(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("LaunchCheckAct: 任务结束")
        return True


@AgentServer.custom_action("FocusEnergyAct")
class FocusEnergyAct(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("FocusEnergyAct: 点击聚能")
        context.controller.post_click(62, 633).wait()
        return True


__all__ = [
    "AutoLaunchAct",
    "LaunchCheckAct",
    "FocusEnergyAct",
]
