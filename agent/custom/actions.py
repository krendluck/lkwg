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

        detail = _parse_detail(reco_detail)
        next_num = detail.get("next_num")
        key_code = detail.get("key_code")
        _log(f"Act 解析 detail: next_num={next_num} key_code={key_code}")
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

def _parse_detail(reco_detail) -> dict:
    detail = {}
    if reco_detail is None:
        return detail

    raw = reco_detail.raw_detail
    _log(f"Act _parse_detail: raw_detail type={type(raw).__name__}")

    if isinstance(raw, dict):
        # 框架已经把结果解析成了字典，从 best.detail 里提取我们塞进去的 JSON 字符串
        best = raw.get("best", {})
        inner_detail = best.get("detail", "")
        if isinstance(inner_detail, str) and inner_detail:
            try:
                detail = json.loads(inner_detail)
                _log(f"Act _parse_detail: 从 best.detail 解析成功 -> {detail}")
            except Exception as e:
                _log(f"Act _parse_detail: 从 best.detail 解析失败 -> {e}")
        else:
            _log("Act _parse_detail: raw 是字典但未找到有效的 best.detail")
    elif isinstance(raw, str):
        try:
            detail = json.loads(raw)
            _log(f"Act _parse_detail: 从字符串解析成功 -> {detail}")
        except Exception as e:
            _log(f"Act _parse_detail: 从字符串解析失败 -> {e}")

    _log(f"Act _parse_detail: 最终 detail={detail}")
    return detail