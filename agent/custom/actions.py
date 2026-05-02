"""
游戏基础动作模块

包含自动登录和聚能两个简单 CustomAction。
这些动作通过 context.controller 直接操控游戏窗口（点击坐标）。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import json
import os
import time


def _log(msg):
    os.makedirs("debug", exist_ok=True)
    with open(os.path.join("debug", "release_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")


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


@AgentServer.custom_action("AutoReleasePetAct")
class AutoReleasePetAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        reco_detail = argv.reco_detail
        _log(f"Act run 开始 reco_detail={reco_detail}")

        if reco_detail is None:
            _log("Act 返回: reco_detail is None")
            return False

        _log(f"Act reco_detail.hit={reco_detail.hit} box={reco_detail.box} raw_detail={reco_detail.raw_detail}")

        if not reco_detail.hit:
            _log("Act 返回: reco_detail.hit 为 False")
            return False

        # ====== 新解析逻辑：从 best_result.detail 取逗号分隔的字符串 ======
        raw = reco_detail.raw_detail
        _log(f"Act raw_detail type={type(raw).__name__} raw={raw}")

        detail_str = ""
        if isinstance(raw, dict):
            best = raw.get("best", {})
            detail_str = best.get("detail", "")
            _log(f"Act 从 best.detail 取出: '{detail_str}'")

        next_num = None
        key_code = None

        if detail_str and "," in detail_str:
            parts = detail_str.split(",")
            try:
                next_num = int(parts[0]) if parts[0] != "None" else None
                key_code = int(parts[1]) if parts[1] != "None" else None
                _log(f"Act 解析成功: next_num={next_num} key_code={key_code}")
            except Exception as e:
                _log(f"Act 解析失败: {e}")
        else:
            _log(f"Act detail_str 为空或格式错误: '{detail_str}'")

        if next_num is None:
            _log("Act 返回: next_num is None")
            return False

        _log(f"Act 按键: post_click_key({key_code})")
        context.controller.post_click_key(key_code).wait()
        _log("Act 返回: True")
        return True


__all__ = [
    "AutoLaunchAct",
    "FocusEnergyAct",
    "AutoReleasePetAct",
]