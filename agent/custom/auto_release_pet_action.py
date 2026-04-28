import re

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("AutoReleasePetAction")
class AutoReleasePetAction(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        detail = argv.reco_detail or ""
        print(f"AutoReleasePetAction: detail={detail}")

        if detail == "in_battle":
            print("AutoReleasePetAction: 战斗中，等待离开")
            return True

        if detail == "not_found" or detail == "template_not_found":
            print("AutoReleasePetAction: 未找到标志，初始化放出")
            context.controller.post_click_key(50).wait()
            return True

        match = re.search(r'next:(\S+)', detail)
        if not match:
            print("AutoReleasePetAction: 未识别到有效动作")
            return True

        next_action = match.group(1)

        if next_action.isdigit():
            num = int(next_action)
            print(f"AutoReleasePetAction: 放出宠物 {num}")
            context.controller.post_click_key(48 + num).wait()
        elif next_action == "switch":
            print("AutoReleasePetAction: 切换宠物")
            context.controller.post_click_key(50).wait()
        else:
            print(f"AutoReleasePetAction: 未知动作 {next_action}")

        return True