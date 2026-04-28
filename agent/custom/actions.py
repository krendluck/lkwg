import json
import random
import time
import re

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


@AgentServer.custom_action("battle_run")
class BattleRunAction(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            payload = json.loads(argv.custom_action_param or "{}")
            seconds = payload.get("fixed_seconds", 0)
        except:
            seconds = 0
        print(f"battle_run: sleep {seconds}s")
        time.sleep(seconds)
        return True


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


@AgentServer.custom_action("BattleRunAct")
class BattleRunAct(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("BattleRunAct: 点击确认脱离")
        context.controller.post_click(743, 594).wait()
        return True


__all__ = [
    "BattleRunAction",
    "AutoLaunchAct",
    "LaunchCheckAct",
    "FocusEnergyAct",
    "BattleRunAct",
]