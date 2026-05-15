import time

import numpy as np

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from ..interception_controller import get_controller
from .general import _update_image_size
from .auto_battle import _expand_skill_order, BACKPACK_ITEMS, _BACKPACK_ITEM_LABELS, CHAR_TO_VK, MAIN_ACTIONS

_VK_Z = 0x5A
_VK_SPACE = 0x20
_VK_W = 0x57
_VK_F = 0x46
_VK_ESC = 0x1B

_Z_ROI = [631, 634, 13, 15]
_SPECIAL_SPACE_ROI = [640, 276, 553, 243]
_TREASURE_OCR_ROI = [801, 367, 87, 21]

_MARK_ICON_POS = (690, 372)
_MARK_COLOR_ROI = [675, 331, 38, 7]
_MARK_COLOR_LOWER = np.array([0, 115, 210], dtype=np.uint8)
_MARK_COLOR_UPPER = np.array([0, 127, 218], dtype=np.uint8)
_MARK_CONFIRM_ROI = [719, 582, 44, 21]

_HOLD_W_TIMEOUT = 15


@AgentServer.custom_action("BossBattleReset")
class BossBattleReset(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        BossBattleAct._skill_index = 0
        BossBattleAct._round_count = 0
        print("[BossBattle] 状态重置")
        return True


@AgentServer.custom_action("BossBattleAct")
class BossBattleAct(CustomAction):

    _skill_index = 0
    _round_count = 0

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        ic = get_controller()

        node_obj = context.get_node_object("BossBattle_WaitSkill1")
        attach = getattr(node_obj, "attach", {}) if node_obj else {}
        skill_order = attach.get("skill_order", "||1x")
        skill_order = _expand_skill_order(skill_order.strip())
        special_skill_order = attach.get("special_skill_order", "1")
        special_skill_order = _expand_skill_order(special_skill_order.strip())

        ctrl.post_screencap().wait()
        image = ctrl.cached_image
        if image is not None:
            z_result = context.run_recognition(
                "BossZDetect",
                image,
                pipeline_override={
                    "BossZDetect": {
                        "recognition": "OCR",
                        "roi": _Z_ROI,
                        "expected": ["z", "Z"],
                    }
                },
            )
            if z_result is not None and z_result.hit:
                print("[BossBattle] 检测到 z，进入特殊阶段")
                return self._exec_special_phase(context, ctrl, ic, special_skill_order)

        if not skill_order:
            return False

        idx = BossBattleAct._skill_index
        if idx >= len(skill_order):
            BossBattleAct._skill_index = 0
            idx = 0
        BossBattleAct._round_count += 1

        print(f"[BossBattle] 回合{BossBattleAct._round_count}, 技能序列: {skill_order}, 当前位置: {idx}")

        while idx < len(skill_order):
            ch = skill_order[idx]
            if ch in ("q", "Q"):
                idx = self._exec_backpack(context, ic, skill_order, idx)
                continue
            if ch in MAIN_ACTIONS:
                label = {"1": "技能1", "2": "技能2", "3": "技能3", "4": "技能4",
                          "x": "聚能", "X": "聚能"}.get(ch, ch)
                print(f"[BossBattle] >>> {label} ({ch})")
                vk = CHAR_TO_VK.get(ch)
                if vk is not None:
                    ic.click_key(vk)
                    time.sleep(0.3)
                idx += 1
                BossBattleAct._skill_index = idx
                return True
            print(f"[BossBattle] 跳过未知字符: {ch}")
            idx += 1
            BossBattleAct._skill_index = idx

        BossBattleAct._skill_index = 0
        return False

    def _exec_special_phase(self, context, ctrl, ic, special_skill_order):
        if not special_skill_order:
            print("[BossBattle] 特殊阶段技能顺序为空，跳过")
            return True

        print(f"[BossBattle] 特殊阶段技能顺序: {special_skill_order}")

        idx = 0
        while idx < len(special_skill_order):
            ctrl.post_screencap().wait()
            image = ctrl.cached_image
            if image is None:
                time.sleep(0.3)
                continue

            result = context.run_recognition(
                "BossSpecialSpaceDetect",
                image,
                pipeline_override={
                    "BossSpecialSpaceDetect": {
                        "recognition": "OCR",
                        "roi": _SPECIAL_SPACE_ROI,
                        "expected": ["space", "Space"],
                    }
                },
            )

            if result is not None and result.hit:
                print("[BossBattle] 检测到 space，按空格释放")
                ic.click_key(_VK_SPACE)
                time.sleep(3)
                return False
            
            time.sleep(0.3)
            
            ch = special_skill_order[idx]
            if ch in ("q", "Q"):
                idx = self._exec_backpack(context, ic, special_skill_order, idx)
                continue
            if ch in MAIN_ACTIONS:
                label = {"1": "技能1", "2": "技能2", "3": "技能3", "4": "技能4",
                          "x": "聚能", "X": "聚能"}.get(ch, ch)
                vk = CHAR_TO_VK.get(ch)
                if vk is not None:
                    print(f"[BossBattle] >>> 特殊阶段 {label} ({ch})")
                    ic.click_key(vk)
                    time.sleep(0.3)
                idx += 1
                continue
            if ch in ("r", "R"):
                idx += 1
                print("[BossBattle] >>> 关闭背包 (r)")
                context.run_task("BossBattle_WaitBackpackR")
                time.sleep(0.5)
                continue
            print(f"[BossBattle] 特殊阶段跳过未知字符: {ch}")
            idx += 1

        return True

    def _exec_backpack(self, context, ic, skill_order, start_idx):
        print("[BossBattle] >>> 打开背包 (q)")
        ic.click_key(CHAR_TO_VK["q"])
        time.sleep(0.8)

        idx = start_idx + 1
        while idx < len(skill_order):
            ch = skill_order[idx]
            if ch in BACKPACK_ITEMS:
                label = _BACKPACK_ITEM_LABELS.get(ch, ch)
                print(f"[BossBattle] >>> 使用{label} ({ch})")
                vk = BACKPACK_ITEMS[ch]
                ic.click_key(vk)
                time.sleep(0.8)
                idx += 1
            elif ch in ("r", "R"):
                idx += 1
                BossBattleAct._skill_index = idx
                print("[BossBattle] >>> 等待R出现并关闭背包 (r)")
                context.run_task("BossBattle_WaitBackpackR")
                context.run_task("BossBattle_WaitSkill1")
                return idx
            elif ch in ("q", "Q"):
                BossBattleAct._skill_index = idx
                print("[BossBattle] >>> 关闭背包后重新打开 (未匹配r，自动关闭)")
                context.run_task("BossBattle_WaitBackpackR")
                context.run_task("BossBattle_WaitSkill1")
                return idx
            else:
                print(f"[BossBattle] 背包内遇到非物品字符: {ch}，自动关闭背包")
                BossBattleAct._skill_index = idx
                context.run_task("BossBattle_WaitBackpackR")
                context.run_task("BossBattle_WaitSkill1")
                return idx

        BossBattleAct._skill_index = idx
        print("[BossBattle] >>> 等待R出现并关闭背包 (r)")
        context.run_task("BossBattle_WaitBackpackR")
        context.run_task("BossBattle_WaitSkill1")
        return idx


@AgentServer.custom_action("BossHoldWAct")
class BossHoldWAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        ic = get_controller()

        print("[BossBattle] 按住 W 行走...")
        ic.key_down(_VK_W)

        start_time = time.time()
        found = False
        while time.time() - start_time < _HOLD_W_TIMEOUT:
            ctrl.post_screencap().wait()
            image = ctrl.cached_image
            if image is None:
                time.sleep(0.2)
                continue

            result = context.run_recognition(
                "BossTreasureDetect",
                image,
                pipeline_override={
                    "BossTreasureDetect": {
                        "recognition": "OCR",
                        "roi": _TREASURE_OCR_ROI,
                        "expected": ["接触群星之遗"],
                    }
                },
            )
            if result is not None and result.hit:
                print("[BossBattle] 检测到接触群星之遗，松开 W")
                ic.key_up(_VK_W)
                found = True
                break

            time.sleep(0.2)

        if not found:
            print("[BossBattle] 超时未检测到接触群星之遗，松开 W 并结束")
            ic.key_up(_VK_W)
            return False

        return True


@AgentServer.custom_action("BossUseMarkAct")
class BossUseMarkAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        node_obj = context.get_node_object("BossBattle_UseMark")
        attach = getattr(node_obj, "attach", {}) if node_obj else {}
        use_mark = str(attach.get("use_mark", "false")).lower() == "true"

        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        ic = get_controller()

        for attempt in range(2):
            print(f"[BossBattle] >>> 点击印记图标 (尝试 {attempt + 1}/2)")

            ctrl.post_screencap().wait()
            image = ctrl.cached_image
            if image is None:
                print("[BossBattle] 截图失败，跳过印记")
                ic.click_key(_VK_ESC)
                time.sleep(0.5)
                return True

            result = context.run_recognition(
                "QieYueDetect",
                image,
                pipeline_override={
                    "QieYueDetect": {
                        "recognition": "TemplateMatch",
                        "template": "Battle/QieYue.png",
                        "roi": [575, 307, 129, 112],
                    }
                },
            )
            if result is not None and result.hit:
                print("[BossBattle] 检测到契约印记，进行确认")
                break
            else:
                print("[BossBattle] 未检测到契约印记，退出")
            # bgr = np.asarray(image, dtype=np.uint8)
            # x, y, w, h = _MARK_COLOR_ROI
            # roi = bgr[y:y + h, x:x + w]
            # lower = np.all(roi >= _MARK_COLOR_LOWER, axis=2)
            # upper = np.all(roi <= _MARK_COLOR_UPPER, axis=2)
            # if np.any(lower & upper):
            #     print("[BossBattle] 印记颜色检测通过")
            #     break
            # print(f"[BossBattle] 印记颜色检测未通过 (尝试 {attempt + 1}/2)")

        confirm_result = context.run_recognition(
            "BossMarkConfirmDetect",
            image,
            pipeline_override={
                "BossMarkConfirmDetect": {
                    "recognition": "OCR",
                    "roi": _MARK_CONFIRM_ROI,
                    "expected": ["确认"],
                }
            },
        )
        if confirm_result is not None and confirm_result.hit:
            box = confirm_result.box
            if box:
                cx = box[0] + box[2] // 2
                cy = box[1] + box[3] // 2
                print(f"[BossBattle] >>> 点击确认 ({cx}, {cy})")
                ic.click(cx, cy)
                time.sleep(1)

        print("[BossBattle] >>> 按 ESC 退出奖励界面")
        ic.click_key(_VK_ESC)
        time.sleep(0.5)

        return True