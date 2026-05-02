"""
自动释放宠物 - 统一 Action 模块

将识别和动作合并为单一 CustomAction，消除了 Recognition→Action 之间的 detail 传递问题。
整个流程：检测已释放槽位 → 计算按键码 → 直接发送按键，全部在同一个 run() 中完成。

游戏中的宠物槽位对应键盘按键：
  槽位2 → 数字键2 (VK=50)
  槽位3 → 数字键3 (VK=51)
  槽位4 → 数字键4 (VK=52)
  槽位5 → 数字键5 (VK=53)
  槽位6 → 数字键6 (VK=54)
数字键的虚拟键码 = 48 + 数字，所以按键码 = 48 + pet_num

检测逻辑：
  对每个宠物槽位，在截图的 ROI 区域做模板匹配（与 status.png 比较），
  匹配成功（hit=True）表示该槽位的宠物已释放（状态图标出现），
  然后找到编号最小的未释放槽位，按下对应的数字键来选中它放宠。
  如果所有槽位都已释放，则按数字键2（切换页面继续寻找）。

Pipeline 配置：
  AutoReleasePet_Entry (DirectHit) → AutoReleasePetAction → AutoReleasePet_Loop → AutoReleasePet_Entry (循环)
  不再需要单独的 DoReleaseKey 节点，按键直接在 Action 中完成。
"""

import json
import os
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("AutoReleasePetAction")
class AutoReleasePetAction(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 解析 Pipeline 中 custom_action_param 传入的 JSON 参数
        # 例如: {"slots":[[95,132,23,18],...], "match_threshold":0.7, "debug_log":true}
        try:
            param = json.loads(argv.custom_action_param or "{}")
        except Exception:
            param = {}

        debug_log = param.get("debug_log", False)
        # 每个宠物槽位在截图中的检测区域 [x, y, width, height]
        # 默认5个槽位分别对应宠物2~6
        slots = param.get("slots", [
            [95, 132, 23, 18],
            [95, 186, 23, 18],
            [95, 240, 23, 18],
            [95, 294, 23, 18],
            [95, 348, 23, 18],
        ])
        match_threshold = param.get("match_threshold", 0.7)

        # 日志文件句柄，debug_log=True 时写入 debug/release_log.txt
        logf = None

        def _log(msg):
            line = f"[{time.strftime('%H:%M:%S')}] {msg}"
            if logf:
                logf.write(line + "\n")
                logf.flush()

        if debug_log:
            os.makedirs("debug", exist_ok=True)
            logf = open(os.path.join("debug", "release_log.txt"), "a")
            _log("=== start ===")

        # 遍历每个槽位，用模板匹配检测该槽位是否已释放（匹配到状态图标=已释放）
        released_nums = set()

        for i, slot in enumerate(slots):
            pet_num = i + 2  # 槽位索引0对应宠物2
            entry = f"pet{pet_num}_check"

            try:
                # 动态创建一个 TemplateMatch 识别任务，指定 ROI 和阈值
                # override_pipeline 会临时添加/覆盖 pipeline 中的任务定义
                context.override_pipeline({
                    entry: {
                        "recognition": "TemplateMatch",
                        "template": "Custom/status.png",
                        "roi": slot,
                        "threshold": match_threshold,
                    }
                })
                # 用当前截图执行识别，返回匹配结果
                match_result = context.run_recognition(entry, argv.image)
            except Exception as e:
                _log(f"pet_{pet_num} EXCEPTION: {e}")
                continue

            # hit=True 表示在该区域匹配到了 status.png 模板，即此槽位宠物已释放
            hit = match_result is not None and match_result.hit
            _log(f"pet_{pet_num} hit={hit}")

            if hit:
                released_nums.add(pet_num)

        # 根据检测结果决定要按哪个键
        if released_nums:
            unreleased = [n for n in range(2, 7) if n not in released_nums]
            if unreleased:
                # 有未释放的槽位 → 选编号最小的，按对应数字键放入宠物
                next_num = min(unreleased)
                key_code = 48 + next_num  # 数字键VK码: '2'=50, '3'=51, ...
            else:
                # 所有槽位都已释放 → 按数字键2切换到下一页继续放宠
                next_num = "switch"
                key_code = 50  # 数字键2
        else:
            # 没检测到任何已释放槽位 → 按数字键2（默认操作/切换页面）
            next_num = None
            key_code = 50  # 数字键2

        _log(f"released={list(sorted(released_nums))}, next={next_num}, key_code={key_code}")

        # 通过 MaaFramework 控制器直接发送按键
        controller = context.tasker.controller
        controller.post_click_key(key_code).wait()
        _log(f"pressed key_code={key_code}")

        if logf:
            logf.close()

        return True